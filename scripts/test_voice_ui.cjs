// Dependency-free regression checks for the actual browser scripts.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../static/voice.js'), 'utf8');
const deferred = () => { let resolve, reject; const promise = new Promise((a, b) => { resolve = a; reject = b; }); return { promise, resolve, reject }; };
const flush = async () => { for (let i = 0; i < 12; i++) await Promise.resolve(); };

class Element extends EventTarget {
    constructor() { super(); this.dataset = {}; this.classList = { toggle() {}, add() {} }; this.value = ''; this.textContent = ''; this.checked = true; this.disabled = false; }
    setAttribute() {}
    focus() { this.focused = true; }
}

function fixture() {
    const elements = new Map();
    const el = id => { if (!elements.has(id)) elements.set(id, new Element()); return elements.get(id); };
    const requests = [], recorders = [], audios = [], utterances = [], timers = new Map(), intervals = new Map();
    const microphone = deferred();
    let micCalls = 0, stoppedTracks = 0, time = 1000, nextTimer = 1;
    const stream = { getTracks: () => [{ stop: () => stoppedTracks++ }] };
    class Recorder extends EventTarget {
        static isTypeSupported() { return true; }
        constructor() { super(); this.state = 'inactive'; this.mimeType = 'audio/webm'; recorders.push(this); }
        start() { this.state = 'recording'; }
        stop() {
            this.state = 'inactive';
            queueMicrotask(() => {
                const event = new Event('dataavailable'); event.data = new Blob(['synthetic audio']);
                this.dispatchEvent(event); this.dispatchEvent(new Event('stop'));
            });
        }
    }
    class Audio extends EventTarget {
        constructor(src) { super(); this.src = src; audios.push(this); }
        play() { this.pending = deferred(); return this.pending.promise; }
        pause() {}
    }
    class Utterance extends EventTarget { constructor(text) { super(); this.text = text; } }
    const window = new EventTarget();
    Object.assign(window, {
        location: { search: '', hostname: 'localhost' }, performance: { now: () => time },
        localStorage: { getItem: () => null, setItem() {} }, MediaRecorder: Recorder,
        SpeechSynthesisUtterance: Utterance,
        speechSynthesis: { cancel() {}, speak: utterance => utterances.push(utterance) },
        setTimeout: fn => { const id = nextTimer++; timers.set(id, fn); return id; }, clearTimeout: id => timers.delete(id),
        setInterval: fn => { const id = nextTimer++; intervals.set(id, fn); return id; }, clearInterval: id => intervals.delete(id),
        sendMessageFromVoice: async text => { window.sent = text; window.ConversationVoice.onThinking({ source: 'voice' }); return { success: true }; }
    });
    vm.runInNewContext(source, {
        window, document: { body: { dataset: { page: 'conversation' } }, getElementById: el },
        navigator: { mediaDevices: { getUserMedia: () => { micCalls++; return microphone.promise; } } },
        MediaRecorder: Recorder, Audio, Blob, FormData, Event, AbortController, URLSearchParams, URL, Date,
        console: { error() {} }, fetch: (url, options) => { const pending = deferred(); requests.push({ url, options, ...pending }); return pending.promise; }
    });
    const click = id => { if (!el(id).disabled) el(id).dispatchEvent(new Event('click')); };
    const respond = async (request, data, ok = true) => { request.resolve({ ok, json: async () => data }); await flush(); };
    return { window, el, click, microphone, stream, requests, recorders, audios, utterances, timers, intervals, respond,
        micCalls: () => micCalls, stoppedTracks: () => stoppedTracks, advance: seconds => { time += seconds * 1000; for (const fn of intervals.values()) fn(); } };
}

async function tests() {
    let f = fixture();
    f.click('mic-btn'); f.click('mic-btn');
    assert.equal(f.micCalls(), 1, 'double tap while permission is pending opens only one microphone');
    f.click('stop-speaking-button'); f.microphone.resolve(f.stream); await flush();
    assert.equal(f.stoppedTracks(), 1, 'late permission grant releases its microphone');
    assert.equal(f.recorders.length, 0);
    assert.equal(f.el('voice-debug-panel').hidden, true, 'localhost does not expose diagnostics by default');

    f = fixture(); f.click('mic-btn'); f.microphone.resolve(f.stream); await flush();
    assert.equal(f.el('mic-btn').textContent, '结束并发送');
    f.click('mic-btn'); await flush();
    assert.equal(f.requests[0].url, '/api/stt');
    assert.ok(f.stoppedTracks() > 0, 'tracks stop before transcription');
    f.click('stop-speaking-button');
    assert.equal(f.requests[0].options.signal.aborted, true);
    await f.respond(f.requests[0], { text: 'a canceled transcript' });
    assert.equal(f.window.sent, undefined, 'canceled transcription never submits a chat');

    f = fixture(); f.window.ConversationVoice.onThinking();
    f.window.ConversationVoice.handleAssistantReply('hello');
    f.click('stop-speaking-button');
    await f.respond(f.requests[0], { audio_base64: 'AAAA' });
    assert.equal(f.audios.length, 0, 'late TTS response cannot restart stopped playback');

    f = fixture(); f.window.ConversationVoice.onThinking();
    f.click('stop-speaking-button');
    assert.equal(f.el('device-dock-status').dataset.state, 'thinking', 'chat remains pending when muting its reply');
    f.window.ConversationVoice.handleAssistantReply('only text');
    assert.equal(f.requests.length, 0);
    assert.equal(f.el('device-dock-status').dataset.state, 'idle');

    f = fixture(); f.window.ConversationVoice.handleAssistantReply('hello');
    await f.respond(f.requests[0], { audio_base64: 'AAAA' });
    assert.equal(f.el('device-dock-status').dataset.state, 'thinking', 'preparing audio is not playing');
    assert.ok(!f.el('tts-fallback-status').textContent.includes('已朗读'));
    const audio = f.audios[0]; audio.dispatchEvent(new Event('playing'));
    assert.equal(f.el('device-dock-status').dataset.state, 'speaking');
    f.click('stop-speaking-button'); audio.pending.reject(new Error('interrupted')); await flush();
    assert.equal(f.utterances.length, 0, 'rejected canceled play must not start browser fallback');

    f = fixture(); f.window.ConversationVoice.handleAssistantReply('hello');
    await f.respond(f.requests[0], { fallback: true });
    const utterance = f.utterances[0]; f.click('stop-speaking-button');
    for (const name of ['start', 'end', 'error']) utterance.dispatchEvent(new Event(name));
    assert.equal(f.el('chat-status-text').textContent, '已停止', 'stale speech callbacks cannot change stopped state');

    f = fixture(); f.window.ConversationVoice.handleAssistantReply('hello');
    f.el('tts-enabled-toggle').checked = false;
    f.el('tts-enabled-toggle').dispatchEvent(new Event('change'));
    await f.respond(f.requests[0], { fallback: true });
    assert.equal(f.utterances.length, 0, 'disabling speech cancels pending synthesis');

    f = fixture(); f.click('mic-btn'); f.microphone.resolve(f.stream); await flush();
    f.advance(60); await flush();
    assert.equal(f.requests.length, 1, 'recording limit ends and sends exactly once');
    assert.equal(f.intervals.size, 0);
    await f.respond(f.requests[0], { error: '语音服务尚未配置' }, false);
    for (const fn of f.timers.values()) fn();
    assert.equal(f.el('composer-help-text').textContent, '语音服务尚未配置', 'errors persist for the user');
    f.window.ConversationVoice.handleAssistantReply('TTS can still work');
    assert.equal(f.requests[1].url, '/api/tts', 'ASR failure does not disable TTS');

    f = fixture(); f.click('mic-btn'); f.microphone.resolve(f.stream); await flush();
    f.window.ConversationVoice.onThinking({ source: 'text' }); await flush();
    assert.equal(f.requests.length, 0, 'typing during recording discards audio instead of sending a second turn');
    assert.equal(f.intervals.size, 0);

    f = fixture(); f.click('mic-btn'); f.microphone.resolve(f.stream); await flush();
    f.window.dispatchEvent(new Event('pagehide')); await flush();
    assert.ok(f.stoppedTracks() > 0); assert.equal(f.requests.length, 0); assert.equal(f.intervals.size, 0);

    f = fixture(); f.window.ConversationVoice.handleAssistantReply('hello');
    await f.respond(f.requests[0], { fallback: true });
    for (const fn of [...f.timers.values()]) fn();
    assert.equal(f.el('device-dock-status').dataset.state, 'idle', 'device TTS that never starts cannot lock controls');
    f = fixture(); f.click('mic-btn'); f.window.ConversationVoice.setIdle();
    f.microphone.resolve(f.stream); await flush();
    assert.equal(f.recorders.length, 0, 'reset also cancels pending microphone permission');

    const script = fs.readFileSync(path.join(__dirname, '../static/script.js'), 'utf8');
    const sendSource = script.slice(script.indexOf('async function sendMessage('), script.indexOf('\nfunction getDeviceSettings'));
    const input = new Element(), button = new Element(), pending = deferred(); let requestCount = 0;
    const context = {
        element: id => id === 'input' ? input : button, updateComposerNote() {}, appendMessage() {},
        window: { ConversationVoice: { onThinking() {}, onError() {} }, performance: { now: () => 10 }, setTimeout() {}, clearTimeout() {} },
        currentLogs: [], getCurrentMode: () => 'alzheimer', formatLocalTimestamp: () => '', renderAll() {},
        legacyProfileUserId: () => null, currentCaregiverPatientId: 'test', currentChatSessionId: null,
        AbortController, sendButtonDefaultText: '发送', console: { error() {} },
        fetch: () => { requestCount++; return pending.promise; }, Event
    };
    vm.createContext(context); vm.runInContext(sendSource, context);
    input.value = '请保留这句话'; const first = context.sendMessage({ source: 'voice' });
    await context.sendMessage({ message: 'duplicate' });
    assert.equal(requestCount, 1, 'Enter/programmatic sends cannot bypass the in-flight guard');
    pending.reject(new Error('offline')); await first;
    assert.equal(input.value, '请保留这句话', 'failed voice transcript remains editable');
    assert.equal(button.disabled, false); assert.equal(input.disabled, false); assert.ok(!input.focused);
    let keySends = 0;
    context.document = { querySelectorAll: () => [] };
    context.isPage = name => name === 'conversation';
    context.sendMessage = () => keySends++;
    vm.runInContext(script.slice(script.indexOf('function bindPageEvents('), script.indexOf('\nfunction renderAll()')), context);
    context.bindPageEvents();
    const composing = new Event('keydown', { cancelable: true });
    Object.assign(composing, { key: 'Enter', isComposing: true }); input.dispatchEvent(composing);
    assert.equal(keySends, 0, 'Chinese IME confirmation does not submit the draft');
    const enter = new Event('keydown', { cancelable: true }); Object.assign(enter, { key: 'Enter' }); input.dispatchEvent(enter);
    assert.equal(keySends, 1);
    console.log('PASS: voice lifecycle, fallback timeout, reset, IME, duplicate send and draft recovery');
}
tests().catch(error => { console.error(error); process.exitCode = 1; });

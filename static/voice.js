/* Conversation voice helpers for the Alzheimer companion device page.
 * Voice MVP chain:
 * idle -> listening -> thinking -> speaking -> idle
 * MediaRecorder -> /api/stt -> /chat -> /api/tts -> audio playback
 */

(function initConversationVoice() {
    if (document.body?.dataset.page !== "conversation") {
        return;
    }

    const voiceButton = document.getElementById("mic-btn") || document.getElementById("voice-button");
    const stopSpeakingButton = document.getElementById("stop-speaking-button");
    const input = document.getElementById("input");
    const statusText = document.getElementById("chat-status-text");
    const dockStatus = document.getElementById("device-dock-status");
    const helpText = document.getElementById("composer-help-text");
    const ttsToggle = document.getElementById("tts-enabled-toggle");
    const ttsFallbackStatus = document.getElementById("tts-fallback-status");
    const ttsPlayingIndicator = document.getElementById("tts-playing-indicator");
    const stripState = document.getElementById("voice-strip-state");
    const stripStep = document.getElementById("voice-strip-step");
    const stripPlaying = document.getElementById("voice-strip-playing");
    const stripInterruptible = document.getElementById("voice-strip-interruptible");
    const debugPanel = document.getElementById("voice-debug-panel");
    const copyDiagnosticsButton = document.getElementById("voice-debug-copy-button");
    const copyDiagnosticsStatus = document.getElementById("voice-debug-copy-status");

    if (!voiceButton || !stopSpeakingButton || !input || !statusText || !dockStatus || !helpText) {
        return;
    }

    const debugRefs = {
        currentState: document.getElementById("voice-debug-current-state"),
        currentStep: document.getElementById("voice-debug-current-step"),
        errorCode: document.getElementById("voice-debug-error-code"),
        fallbackUsed: document.getElementById("voice-debug-fallback-used"),
        asrProviderModel: document.getElementById("voice-debug-asr-provider-model"),
        ttsProviderModel: document.getElementById("voice-debug-tts-provider-model"),
        asrBlock: document.getElementById("voice-debug-asr-block"),
        chatBlock: document.getElementById("voice-debug-chat-block"),
        ttsBlock: document.getElementById("voice-debug-tts-block"),
        overallBlock: document.getElementById("voice-debug-overall-block"),
        diagnosisBlock: document.getElementById("voice-debug-diagnosis-block"),
        events: document.getElementById("voice-debug-events")
    };

    const defaultHelpText = "点一下开始说话，说完再点一下结束并发送。";
    const defaultStripText = "我会安静陪着你。";
    const stateTextMap = {
        idle: "陪伴中",
        listening: "我在听你说",
        thinking: "我在想一下",
        speaking: "我在说"
    };
    const substageTextMap = {
        idle: "我会安静陪着你。",
        listening: "我在听你说话。",
        requesting_mic: "正在打开麦克风",
        uploading_audio: "我听到了，正在整理。",
        transcribing: "我听到了，正在整理。",
        sending_chat: "我正在想怎么回答你。",
        generating_speech: "正在准备朗读",
        playing_audio: "我正在陪你慢慢说。"
    };
    const recordingMimeCandidates = [
        "audio/webm;codecs=opus",
        "audio/webm",
        "audio/mp4",
        "audio/ogg;codecs=opus"
    ];
    const query = new URLSearchParams(window.location.search);
    const debugEnabled = query.get("voice_debug") === "1"
        || query.get("debugvoice") === "1"
        || query.get("debug") === "1";
    const hasRecorderSupport = Boolean(
        navigator.mediaDevices
        && typeof navigator.mediaDevices.getUserMedia === "function"
        && typeof window.MediaRecorder === "function"
    );
    const hasBrowserSpeechSupport = Boolean(window.speechSynthesis && typeof window.SpeechSynthesisUtterance === "function");

    let currentState = "idle";
    let currentStep = "idle";
    let restoreTimer = null;
    let currentStream = null;
    let mediaRecorder = null;
    let recordedChunks = [];
    let currentAudio = null;
    let currentAudioUrl = "";
    let currentUtterance = null;
    let browserStartTimer = null;
    let discardNextRecording = false;
    let recordingTimer = null;
    let voiceEpoch = 0;
    let speechEpoch = 0;
    let sttController = null;
    let ttsController = null;
    let muteCurrentReply = false;
    let turnStartedAt = 0;
    let recordStartedAt = 0;
    let playbackStartedAt = 0;

    function readTtsEnabled() {
        try {
            return window.localStorage.getItem("conversation_tts_enabled") !== "false";
        } catch {
            return true;
        }
    }

    function updateTtsFallbackStatus(text) {
        if (ttsFallbackStatus) {
            ttsFallbackStatus.textContent = text;
        }
    }

    function isTtsEnabled() {
        return Boolean(ttsToggle?.checked);
    }

    const debugState = {
        current_state: "idle",
        current_step: "idle",
        last_transcript: "",
        user_text_sent_to_chat: "",
        assistant_reply: "",
        error_code: "",
        error_message: "",
        user_friendly_message: defaultHelpText,
        final_status: "idle",
        fallback_used: false,
        asr_provider: "",
        asr_model: "",
        transcribe_error_code: "",
        transcribe_confidence: null,
        requested_provider: "",
        actual_provider: "",
        llm_model: "",
        chat_fallback_used: false,
        chat_fallback_reason: "",
        guard_triggered: false,
        guard_reason: "",
        memory_context_used: null,
        profile_memory_used: null,
        session_memory_used: null,
        long_term_memory_used: null,
        transcribe_diagnosis: null,
        chat_diagnosis: null,
        tts_diagnosis: null,
        tts_provider: "",
        tts_model: "",
        tts_error_code: "",
        metrics: {
            record_duration_ms: null,
            transcribe_latency_ms: null,
            chat_latency_ms: null,
            tts_latency_ms: null,
            playback_duration_ms: null,
            total_voice_turn_ms: null
        },
        events: []
    };

    function clearRestoreTimer() {
        if (restoreTimer) {
            window.clearTimeout(restoreTimer);
            restoreTimer = null;
        }
    }

    function scheduleRestore(delay = 1800) {
        clearRestoreTimer();
        if (helpText.dataset.kind === "warning") return;
        restoreTimer = window.setTimeout(() => {
            setPhase("idle", "idle", "陪伴中", defaultHelpText);
        }, delay);
    }

    function formatProviderModel(provider, model) {
        const left = String(provider || "").trim();
        const right = String(model || "").trim();
        if (!left && !right) {
            return "-";
        }
        return right ? `${left} / ${right}` : left;
    }

    function formatMetricValue(value) {
        if (value === null || value === undefined || value === "") {
            return "-";
        }
        return `${value} ms`;
    }

    function formatMetrics() {
        return [
            `record_duration_ms: ${formatMetricValue(debugState.metrics.record_duration_ms)}`,
            `transcribe_latency_ms: ${formatMetricValue(debugState.metrics.transcribe_latency_ms)}`,
            `chat_latency_ms: ${formatMetricValue(debugState.metrics.chat_latency_ms)}`,
            `tts_latency_ms: ${formatMetricValue(debugState.metrics.tts_latency_ms)}`,
            `playback_duration_ms: ${formatMetricValue(debugState.metrics.playback_duration_ms)}`,
            `total_voice_turn_ms: ${formatMetricValue(debugState.metrics.total_voice_turn_ms)}`
        ].join("\n");
    }

    function formatBlockValue(value) {
        if (value === null || value === undefined || value === "") {
            return "-";
        }
        if (typeof value === "object") {
            return JSON.stringify(value, null, 2);
        }
        return String(value);
    }

    function normalizeDiagnosis(diagnosis) {
        if (!diagnosis || typeof diagnosis !== "object") {
            return null;
        }
        const tags = Array.isArray(diagnosis.tags)
            ? diagnosis.tags.map((tag) => String(tag || "").trim()).filter(Boolean)
            : [];
        return {
            tags,
            primary_issue: diagnosis.primary_issue ? String(diagnosis.primary_issue) : null,
            severity: diagnosis.severity ? String(diagnosis.severity) : "info",
            human_summary: diagnosis.human_summary ? String(diagnosis.human_summary) : "",
            suggested_next_step: diagnosis.suggested_next_step ? String(diagnosis.suggested_next_step) : ""
        };
    }

    function mergeDiagnosis() {
        const severityRank = {
            info: 0,
            warning: 1,
            error: 2
        };
        const sections = [
            debugState.transcribe_diagnosis,
            debugState.chat_diagnosis,
            debugState.tts_diagnosis
        ].filter(Boolean);
        if (!sections.length) {
            return {
                tags: [],
                primary_issue: null,
                severity: "info",
                human_summary: "No diagnosis has been collected for this turn yet.",
                suggested_next_step: "Run one voice turn or one chat turn to populate diagnostics."
            };
        }

        const tags = [];
        let chosen = sections[0];
        sections.forEach((section) => {
            section.tags.forEach((tag) => {
                if (!tags.includes(tag)) {
                    tags.push(tag);
                }
            });
            if ((severityRank[section.severity] || 0) > (severityRank[chosen.severity] || 0)) {
                chosen = section;
            }
        });

        return {
            tags,
            primary_issue: chosen.primary_issue,
            severity: chosen.severity,
            human_summary: chosen.human_summary,
            suggested_next_step: chosen.suggested_next_step
        };
    }

    function parseDiagnosisHeaders(response) {
        const tagsHeader = String(response.headers.get("X-Voice-Diagnosis-Tags") || "").trim();
        const primaryIssue = String(response.headers.get("X-Voice-Diagnosis-Primary-Issue") || "").trim();
        const severity = String(response.headers.get("X-Voice-Diagnosis-Severity") || "").trim();
        const humanSummary = String(response.headers.get("X-Voice-Diagnosis-Human-Summary") || "").trim();
        const nextStep = String(response.headers.get("X-Voice-Diagnosis-Next-Step") || "").trim();
        if (!tagsHeader && !primaryIssue && !severity && !humanSummary && !nextStep) {
            return null;
        }
        return normalizeDiagnosis({
            tags: tagsHeader ? tagsHeader.split(",") : [],
            primary_issue: primaryIssue || null,
            severity: severity || "info",
            human_summary: humanSummary,
            suggested_next_step: nextStep
        });
    }

    function buildTurnDiagnosticsExport() {
        return {
            asr: {
                transcribed_text: debugState.last_transcript || null,
                transcribe_provider: debugState.asr_provider || null,
                transcribe_model: debugState.asr_model || null,
                transcribe_latency_ms: debugState.metrics.transcribe_latency_ms,
                transcribe_error_code: debugState.transcribe_error_code || null,
                confidence: debugState.transcribe_confidence,
                diagnosis: debugState.transcribe_diagnosis
            },
            chat: {
                user_text_sent_to_chat: debugState.user_text_sent_to_chat || null,
                assistant_reply: debugState.assistant_reply || null,
                requested_provider: debugState.requested_provider || null,
                actual_provider: debugState.actual_provider || null,
                llm_model: debugState.llm_model || null,
                fallback_used: debugState.chat_fallback_used,
                fallback_reason: debugState.chat_fallback_reason || null,
                guard_triggered: debugState.guard_triggered,
                guard_reason: debugState.guard_reason || null,
                memory_context_used: debugState.memory_context_used,
                profile_memory_used: debugState.profile_memory_used,
                session_memory_used: debugState.session_memory_used,
                long_term_memory_used: debugState.long_term_memory_used,
                chat_latency_ms: debugState.metrics.chat_latency_ms,
                diagnosis: debugState.chat_diagnosis
            },
            tts: {
                tts_provider: debugState.tts_provider || null,
                tts_model: debugState.tts_model || null,
                tts_latency_ms: debugState.metrics.tts_latency_ms,
                tts_error_code: debugState.tts_error_code || null,
                diagnosis: debugState.tts_diagnosis
            },
            overall: {
                current_state: debugState.current_state,
                current_step: debugState.current_step,
                total_voice_turn_ms: debugState.metrics.total_voice_turn_ms,
                final_status: debugState.final_status || null,
                last_error_code: debugState.error_code || null,
                user_friendly_message: debugState.user_friendly_message || null,
                fallback_used: debugState.fallback_used,
                diagnosis: mergeDiagnosis()
            },
            diagnosis: mergeDiagnosis()
        };
    }

    function buildDiagnosticBlock(section) {
        return Object.entries(section)
            .map(([key, value]) => `${key}: ${formatBlockValue(value)}`)
            .join("\n");
    }

    function renderDebugPanel() {
        if (!debugPanel || !debugEnabled) {
            return;
        }

        if (debugRefs.currentState) {
            debugRefs.currentState.textContent = debugState.current_state || "-";
        }
        if (debugRefs.currentStep) {
            debugRefs.currentStep.textContent = debugState.current_step || "-";
        }
        if (debugRefs.errorCode) {
            debugRefs.errorCode.textContent = debugState.error_code || "-";
        }
        if (debugRefs.fallbackUsed) {
            debugRefs.fallbackUsed.textContent = String(Boolean(debugState.fallback_used));
        }
        if (debugRefs.asrProviderModel) {
            debugRefs.asrProviderModel.textContent = formatProviderModel(debugState.asr_provider, debugState.asr_model);
        }
        if (debugRefs.ttsProviderModel) {
            debugRefs.ttsProviderModel.textContent = formatProviderModel(debugState.tts_provider, debugState.tts_model);
        }
        const exportPayload = buildTurnDiagnosticsExport();
        if (debugRefs.asrBlock) {
            debugRefs.asrBlock.textContent = buildDiagnosticBlock(exportPayload.asr);
        }
        if (debugRefs.chatBlock) {
            debugRefs.chatBlock.textContent = buildDiagnosticBlock(exportPayload.chat);
        }
        if (debugRefs.ttsBlock) {
            debugRefs.ttsBlock.textContent = buildDiagnosticBlock(exportPayload.tts);
        }
        if (debugRefs.overallBlock) {
            debugRefs.overallBlock.textContent = buildDiagnosticBlock({
                ...exportPayload.overall,
                metrics: formatMetrics(),
                debug_message: debugState.error_message || null
            });
        }
        if (debugRefs.diagnosisBlock) {
            debugRefs.diagnosisBlock.textContent = buildDiagnosticBlock(exportPayload.diagnosis);
        }
        if (debugRefs.events) {
            debugRefs.events.textContent = debugState.events.length
                ? debugState.events.map((event) => `${event.timestamp}  ${event.name}${event.detail ? `  ${event.detail}` : ""}`).join("\n")
                : "-";
        }
    }

    function emitDebugEvent(name, detail = "") {
        const timestamp = new Date().toLocaleTimeString("zh-CN", {
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
            hour12: false
        });
        debugState.events = [
            {
                timestamp,
                name,
                detail: String(detail || "").trim()
            },
            ...debugState.events
        ].slice(0, 10);
        if (debugEnabled) {
            console.debug("[voice]", name, detail);
        }
        renderDebugPanel();
    }

    function renderStatusStrip() {
        if (stripState) {
            stripState.textContent = stateTextMap[currentState] || stateTextMap.idle;
        }
        if (stripStep) {
            stripStep.textContent = substageTextMap[currentStep] || defaultStripText;
        }
        if (stripPlaying) {
            stripPlaying.textContent = currentState === "speaking" ? "播放中 · 可打断" : "未播放";
        }
        if (stripInterruptible) {
            stripInterruptible.textContent = currentState === "thinking" ? "稍等一下" : "可以";
        }
    }

    function setHelpText(text, kind = "") {
        helpText.textContent = text;
        helpText.dataset.kind = kind;
        debugState.user_friendly_message = text;
    }

    function setPhase(state, step = "idle", text = "", help = defaultHelpText, helpKind = "") {
        const nextState = stateTextMap[state] ? state : "idle";
        const nextStep = substageTextMap[step] ? step : nextState;
        currentState = nextState;
        currentStep = nextStep;
        debugState.current_state = nextState;
        debugState.current_step = nextStep;
        dockStatus.dataset.state = nextState;
        dockStatus.dataset.step = nextStep;
        statusText.textContent = text || substageTextMap[nextStep] || stateTextMap[nextState];
        stopSpeakingButton.disabled = nextState === "idle" || (nextStep === "sending_chat" && muteCurrentReply);
        stopSpeakingButton.textContent = nextState === "listening" ? "取消录音"
            : nextStep === "sending_chat" ? "本次不朗读" : "停止";
        voiceButton.disabled = nextState === "thinking";
        voiceButton.textContent = nextState === "listening" ? "结束并发送"
            : nextState === "speaking" ? "打断并说话" : "开始说话";
        voiceButton.setAttribute("aria-label", voiceButton.textContent);
        const timer = document.getElementById("recording-duration");
        if (timer) timer.hidden = nextState !== "listening";
        if (ttsPlayingIndicator) {
            ttsPlayingIndicator.hidden = nextState !== "speaking";
        }
        voiceButton.classList.toggle("is-listening", nextState === "listening");
        voiceButton.setAttribute("aria-pressed", nextState === "listening" ? "true" : "false");
        setHelpText(help, helpKind);
        renderStatusStrip();
        renderDebugPanel();
    }

    function resetTurnMetrics() {
        debugState.metrics = {
            record_duration_ms: null,
            transcribe_latency_ms: null,
            chat_latency_ms: null,
            tts_latency_ms: null,
            playback_duration_ms: null,
            total_voice_turn_ms: null
        };
        debugState.error_code = "";
        debugState.error_message = "";
        debugState.user_friendly_message = defaultHelpText;
        debugState.final_status = "idle";
        debugState.fallback_used = false;
        debugState.last_transcript = "";
        debugState.user_text_sent_to_chat = "";
        debugState.assistant_reply = "";
        debugState.asr_provider = "";
        debugState.asr_model = "";
        debugState.transcribe_error_code = "";
        debugState.transcribe_confidence = null;
        debugState.requested_provider = "";
        debugState.actual_provider = "";
        debugState.llm_model = "";
        debugState.chat_fallback_used = false;
        debugState.chat_fallback_reason = "";
        debugState.guard_triggered = false;
        debugState.guard_reason = "";
        debugState.memory_context_used = null;
        debugState.profile_memory_used = null;
        debugState.session_memory_used = null;
        debugState.long_term_memory_used = null;
        debugState.transcribe_diagnosis = null;
        debugState.chat_diagnosis = null;
        debugState.tts_diagnosis = null;
        debugState.tts_provider = "";
        debugState.tts_model = "";
        debugState.tts_error_code = "";
        renderDebugPanel();
    }

    function applyChatDiagnostics(diagnostics) {
        if (!diagnostics || typeof diagnostics !== "object") {
            return;
        }
        debugState.requested_provider = String(diagnostics.requested_provider || "").trim();
        debugState.actual_provider = String(diagnostics.actual_provider || "").trim();
        debugState.llm_model = String(diagnostics.model || diagnostics.llm_model || "").trim();
        debugState.chat_fallback_used = Boolean(diagnostics.fallback_used);
        debugState.fallback_used = debugState.fallback_used || debugState.chat_fallback_used;
        debugState.chat_fallback_reason = String(diagnostics.fallback_reason || "").trim();
        debugState.guard_triggered = Boolean(diagnostics.guard_triggered);
        debugState.guard_reason = String(diagnostics.guard_reason || "").trim();
        debugState.memory_context_used = diagnostics.memory_context_used ?? null;
        debugState.profile_memory_used = diagnostics.profile_memory_used ?? null;
        debugState.session_memory_used = diagnostics.session_memory_used ?? null;
        debugState.long_term_memory_used = diagnostics.long_term_memory_used ?? null;
        debugState.chat_diagnosis = normalizeDiagnosis(diagnostics.diagnosis);
        if (diagnostics.chat_latency_ms !== undefined && diagnostics.chat_latency_ms !== null) {
            debugState.metrics.chat_latency_ms = diagnostics.chat_latency_ms;
        }
        renderDebugPanel();
    }

    function applyVoiceDiagnosis(stage, diagnosis) {
        const normalized = normalizeDiagnosis(diagnosis);
        if (!normalized) {
            return;
        }
        if (stage === "transcribe") {
            debugState.transcribe_diagnosis = normalized;
        }
        if (stage === "speak") {
            debugState.tts_diagnosis = normalized;
        }
        renderDebugPanel();
    }

    async function copyCurrentDiagnostics() {
        const payload = JSON.stringify(buildTurnDiagnosticsExport(), null, 2);
        try {
            if (navigator.clipboard?.writeText) {
                await navigator.clipboard.writeText(payload);
            } else {
                const temp = document.createElement("textarea");
                temp.value = payload;
                temp.setAttribute("readonly", "true");
                temp.style.position = "absolute";
                temp.style.left = "-9999px";
                document.body.appendChild(temp);
                temp.select();
                document.execCommand("copy");
                document.body.removeChild(temp);
            }
            if (copyDiagnosticsStatus) {
                copyDiagnosticsStatus.textContent = "已复制本次诊断结果。";
            }
            emitDebugEvent("diagnostics_copied");
        } catch (error) {
            console.error(error);
            if (copyDiagnosticsStatus) {
                copyDiagnosticsStatus.textContent = "复制没有成功，请稍后再试。";
            }
            emitDebugEvent("diagnostics_copy_failed", error instanceof Error ? error.message : "unknown");
        }
        if (copyDiagnosticsStatus) {
            window.setTimeout(() => {
                copyDiagnosticsStatus.textContent = " ";
            }, 1800);
        }
    }

    function finalizeTurnMetrics() {
        if (turnStartedAt > 0) {
            debugState.metrics.total_voice_turn_ms = Math.max(0, Math.round((window.performance?.now?.() || Date.now()) - turnStartedAt));
        }
    }

    function resetInputToTranscript(transcript) {
        input.value = transcript;
        input.dispatchEvent(new Event("input", { bubbles: true }));
    }

    function releaseStream() {
        if (currentStream) {
            currentStream.getTracks().forEach((track) => {
                track.stop();
            });
        }
        currentStream = null;
    }

    function cleanupAudioPlayback() {
        window.clearTimeout(browserStartTimer);
        browserStartTimer = null;
        if (currentAudio) {
            const audio = currentAudio;
            currentAudio = null;
            audio.pause();
            audio.src = "";
        }
        if (currentAudioUrl) {
            if (String(currentAudioUrl).startsWith("blob:")) {
                URL.revokeObjectURL(currentAudioUrl);
            }
            currentAudioUrl = "";
        }
        currentUtterance = null;
        if (window.speechSynthesis) {
            window.speechSynthesis.cancel();
        }
    }

    function stopSpeaking(options = {}) {
        speechEpoch += 1;
        ttsController?.abort();
        ttsController = null;
        if (currentState === "speaking" && playbackStartedAt > 0 && !debugState.metrics.playback_duration_ms) {
            debugState.metrics.playback_duration_ms = Math.max(0, Math.round((window.performance?.now?.() || Date.now()) - playbackStartedAt));
        }
        cleanupAudioPlayback();
        playbackStartedAt = 0;
        updateTtsFallbackStatus(isTtsEnabled() ? "朗读已停止" : "语音朗读已关闭");

        if (options.silent) {
            if (!options.preserveState) {
                finalizeTurnMetrics();
                setPhase("idle", "idle", "陪伴中", defaultHelpText);
            }
            return;
        }

        finalizeTurnMetrics();
        setPhase("idle", "idle", "播报已停下", defaultHelpText);
        scheduleRestore(1200);
        emitDebugEvent("stop_speaking", options.reason || "manual");
    }

    function pickRecordingMimeType() {
        if (typeof window.MediaRecorder?.isTypeSupported !== "function") {
            return "";
        }
        return recordingMimeCandidates.find((value) => window.MediaRecorder.isTypeSupported(value)) || "";
    }

    function blobExtension(blobType) {
        const normalizedType = String(blobType || "").split(";", 1)[0].trim().toLowerCase();
        if (normalizedType === "audio/mp4") {
            return "m4a";
        }
        if (normalizedType === "audio/ogg") {
            return "ogg";
        }
        if (normalizedType === "audio/wav") {
            return "wav";
        }
        return "webm";
    }

    async function readErrorPayload(response, fallbackMessage) {
        try {
            const data = await response.json();
            return {
                success: false,
                stage: String(data?.stage || "transcribe").trim(),
                error_code: String(data?.error_code || "").trim(),
                user_friendly_message: String(data?.user_friendly_message || data?.error || data?.detail || fallbackMessage).trim(),
                debug_message: String(data?.debug_message || data?.error_message || data?.error || data?.detail || fallbackMessage).trim(),
                latency_ms: data?.latency_ms ?? null,
                provider: String(data?.provider || "").trim(),
                model: String(data?.model || "").trim(),
                fallback_used: Boolean(data?.fallback_used),
                diagnosis: normalizeDiagnosis(data?.diagnosis)
            };
        } catch (error) {
            console.error(error);
            return {
                success: false,
                stage: "",
                error_code: "",
                user_friendly_message: fallbackMessage,
                debug_message: fallbackMessage,
                latency_ms: null,
                provider: "",
                model: "",
                fallback_used: false,
                diagnosis: null
            };
        }
    }

    function applyVoiceError(payload, fallbackText) {
        const message = String(payload?.user_friendly_message || fallbackText).trim() || fallbackText;
        debugState.error_code = String(payload?.error_code || "").trim();
        debugState.error_message = String(payload?.debug_message || payload?.user_friendly_message || fallbackText).trim();
        debugState.user_friendly_message = message;
        debugState.fallback_used = Boolean(payload?.fallback_used);
        if (payload?.stage === "transcribe") {
            debugState.transcribe_error_code = debugState.error_code;
            debugState.final_status = "transcribe_failed";
        }
        if (payload?.stage === "speak") {
            debugState.tts_error_code = debugState.error_code;
            debugState.final_status = "tts_failed";
        }
        applyVoiceDiagnosis(payload?.stage, payload?.diagnosis);
        if (payload?.provider) {
            if (payload.stage === "transcribe") {
                debugState.asr_provider = payload.provider;
                debugState.asr_model = payload.model || debugState.asr_model;
            }
            if (payload.stage === "speak") {
                debugState.tts_provider = payload.provider;
                debugState.tts_model = payload.model || debugState.tts_model;
            }
        }
        if (payload?.latency_ms !== null && payload?.latency_ms !== undefined) {
            if (payload.stage === "transcribe") {
                debugState.metrics.transcribe_latency_ms = payload.latency_ms;
            }
            if (payload.stage === "speak") {
                debugState.metrics.tts_latency_ms = payload.latency_ms;
            }
        }
        renderDebugPanel();
        emitDebugEvent(`error:${payload?.stage || "unknown"}`, `${debugState.error_code || "unknown"} ${message}`);
        return message;
    }

    function speakWithBrowserFallback(text) {
        if (!hasBrowserSpeechSupport) {
            return false;
        }
        cleanupAudioPlayback();
        const epoch = speechEpoch;
        const utterance = new window.SpeechSynthesisUtterance(String(text || "").trim());
        utterance.lang = "zh-CN";
        utterance.rate = 0.92;
        utterance.pitch = 1;
        utterance.volume = 1;
        currentUtterance = utterance;
        debugState.fallback_used = true;
        debugState.tts_provider = "browser_tts";
        debugState.tts_model = "speechSynthesis";
        debugState.tts_error_code = "";
        updateTtsFallbackStatus("正在尝试设备朗读");

        utterance.addEventListener("start", () => {
            if (currentUtterance !== utterance || epoch !== speechEpoch) return;
            window.clearTimeout(browserStartTimer);
            updateTtsFallbackStatus("正在使用设备朗读");
            playbackStartedAt = window.performance?.now?.() || Date.now();
            setPhase("speaking", "playing_audio", "🔊 播放中...", "当前使用浏览器朗读。");
        });
        utterance.addEventListener("end", () => {
            if (currentUtterance !== utterance || epoch !== speechEpoch) return;
            window.clearTimeout(browserStartTimer);
            updateTtsFallbackStatus("本次朗读已结束");
            debugState.metrics.playback_duration_ms = playbackStartedAt > 0
                ? Math.max(0, Math.round((window.performance?.now?.() || Date.now()) - playbackStartedAt))
                : null;
            playbackStartedAt = 0;
            currentUtterance = null;
            debugState.final_status = "completed_browser_tts";
            finalizeTurnMetrics();
            setPhase("idle", "idle", "陪伴中", defaultHelpText);
        });
        utterance.addEventListener("error", () => {
            if (currentUtterance !== utterance || epoch !== speechEpoch) return;
            window.clearTimeout(browserStartTimer);
            updateTtsFallbackStatus("朗读未完成，回复文字已保留");
            playbackStartedAt = 0;
            currentUtterance = null;
            debugState.tts_error_code = "BROWSER_TTS_FAILED";
            debugState.final_status = "tts_failed";
            finalizeTurnMetrics();
            setPhase("idle", "idle", "这次没有顺利读出来", "浏览器朗读没有成功，文字聊天不受影响。", "warning");
            scheduleRestore();
        });

        browserStartTimer = window.setTimeout(() => {
            if (currentUtterance !== utterance || epoch !== speechEpoch) return;
            cleanupAudioPlayback();
            updateTtsFallbackStatus("朗读未开始，回复文字已保留");
            setPhase("idle", "idle", "设备暂时没有开始朗读", "你可以先看回复文字，或再试一次对话。", "warning");
        }, 15000);
        try {
            window.speechSynthesis.speak(utterance);
        } catch {
            cleanupAudioPlayback();
            updateTtsFallbackStatus("朗读未开始，回复文字已保留");
            return false;
        }
        return true;
    }

    async function requestSpeech(reply, meta = {}) {
        const cleanReply = String(reply || "").trim();
        if (!cleanReply) {
            finalizeTurnMetrics();
            setPhase("idle", "idle", "陪伴中", defaultHelpText);
            return;
        }
        if (!isTtsEnabled() || muteCurrentReply) {
            updateTtsFallbackStatus("本次回复仅显示文字");
            finalizeTurnMetrics();
            setPhase("idle", "idle", "陪伴中", defaultHelpText);
            return;
        }
        stopSpeaking({ silent: true, preserveState: true });
        const epoch = speechEpoch;
        const controller = new AbortController();
        ttsController = controller;
        const timeout = window.setTimeout(() => controller.abort(), 45000);
        cleanupAudioPlayback();
        debugState.assistant_reply = cleanReply;
        debugState.tts_error_code = "";
        if (meta.chatLatencyMs !== undefined) {
            debugState.metrics.chat_latency_ms = meta.chatLatencyMs;
        }
        applyChatDiagnostics(meta.diagnostics);
        setPhase("thinking", "generating_speech", "正在准备朗读", "回复文字已显示；你可以随时停止朗读。");
        updateTtsFallbackStatus("语音尚未播放");
        emitDebugEvent("tts_request_start", cleanReply.slice(0, 36));
        let requestedAudio = null;

        try {
            const ttsStartedAt = window.performance?.now?.() || Date.now();
            const response = await fetch("/api/tts", {
                signal: controller.signal,
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ text: cleanReply })
            });
            const payload = await response.json();
            if (epoch !== speechEpoch) return;
            debugState.metrics.tts_latency_ms = Math.max(0, Math.round((window.performance?.now?.() || Date.now()) - ttsStartedAt));

            if (!response.ok || payload?.fallback) {
                debugState.tts_provider = "browser_tts";
                debugState.tts_model = "speechSynthesis";
                debugState.tts_error_code = "TTS_FALLBACK";
                if (speakWithBrowserFallback(payload?.text || cleanReply)) {
                    return;
                }
                const detail = payload?.reason || "语音播报暂时还没准备好，文字聊天不受影响。";
                setPhase("idle", "idle", "这次先用文字陪你。", detail, "warning");
                scheduleRestore();
                return;
            }

            if (!payload.audio_base64) {
                if (speakWithBrowserFallback(payload.text || cleanReply)) {
                    return;
                }
                setPhase("idle", "idle", "这次先用文字陪你。", "没有拿到语音数据，先继续文字聊天。", "warning");
                scheduleRestore();
                return;
            }

            debugState.error_code = "";
            debugState.error_message = "";
            debugState.fallback_used = false;
            debugState.tts_provider = "minimax";
            debugState.tts_model = "t2a_v2";
            debugState.tts_error_code = "";
            updateTtsFallbackStatus("语音已准备好，等待播放");
            currentAudioUrl = `data:audio/mp3;base64,${payload.audio_base64}`;
            const audio = new Audio(currentAudioUrl);
            requestedAudio = audio;
            currentAudio = audio;

            audio.addEventListener("playing", () => {
                if (currentAudio !== audio) {
                    return;
                }
                playbackStartedAt = window.performance?.now?.() || Date.now();
                updateTtsFallbackStatus("正在朗读回复");
                setPhase("speaking", "playing_audio", "正在朗读", "随时可以停止，或打断后继续说话。");
                emitDebugEvent("playback_started");
            });

            audio.addEventListener("ended", () => {
                if (currentAudio !== audio) {
                    return;
                }
                debugState.metrics.playback_duration_ms = playbackStartedAt > 0
                    ? Math.max(0, Math.round((window.performance?.now?.() || Date.now()) - playbackStartedAt))
                    : null;
                cleanupAudioPlayback();
                playbackStartedAt = 0;
                debugState.final_status = "completed";
                updateTtsFallbackStatus("本次朗读已结束");
                finalizeTurnMetrics();
                setPhase("idle", "idle", "陪伴中", defaultHelpText);
                emitDebugEvent("playback_ended");
            });

            audio.addEventListener("error", () => {
                if (currentAudio !== audio) {
                    return;
                }
                cleanupAudioPlayback();
                playbackStartedAt = 0;
                debugState.error_code = "VOICE_TTS_FAILED";
                debugState.error_message = "Audio playback error in browser";
                debugState.tts_error_code = "VOICE_TTS_FAILED";
                debugState.final_status = "playback_error";
                if (!speakWithBrowserFallback(payload.text || cleanReply)) {
                    finalizeTurnMetrics();
                    setPhase("idle", "idle", "这次没有顺利读出来", "文字聊天不受影响，我们还可以继续。", "warning");
                    scheduleRestore();
                }
                emitDebugEvent("playback_error");
            });

            await audio.play();
        } catch (error) {
            if (epoch !== speechEpoch) return;
            if (requestedAudio && currentAudio !== requestedAudio) return;
            console.error(error);
            cleanupAudioPlayback();
            playbackStartedAt = 0;
            debugState.error_code = "VOICE_UNKNOWN_ERROR";
            debugState.error_message = error instanceof Error ? error.message : "Unknown TTS error";
            debugState.tts_error_code = "VOICE_UNKNOWN_ERROR";
            debugState.final_status = "tts_failed";
            if (!speakWithBrowserFallback(cleanReply)) {
                applyVoiceDiagnosis("speak", {
                    tags: ["tts_failed"],
                    primary_issue: "voice_tts_failed",
                    severity: "warning",
                    human_summary: "The TTS step did not complete cleanly.",
                    suggested_next_step: "Inspect the TTS error and retry with the text reply still visible."
                });
                finalizeTurnMetrics();
                setPhase("idle", "idle", "这次没有顺利读出来", "文字聊天不受影响，我们还可以继续。", "warning");
                scheduleRestore();
            }
            emitDebugEvent("tts_exception", debugState.error_message);
        } finally {
            window.clearTimeout(timeout);
            if (ttsController === controller) ttsController = null;
        }
    }

    async function transcribeAndSend(audioBlob) {
        const epoch = voiceEpoch;
        const controller = new AbortController();
        sttController = controller;
        const timeout = window.setTimeout(() => controller.abort(), 45000);
        const extension = blobExtension(audioBlob.type);
        const filename = `voice-note.${extension}`;

        setPhase("thinking", "uploading_audio", "我听到了，正在整理。", "这句话我来替你发出去。");
        emitDebugEvent("upload_start", `${audioBlob.type || "audio/webm"} ${audioBlob.size} bytes`);

        try {
            const formData = new FormData();
            formData.append("audio", audioBlob, filename);
            const sttStartedAt = window.performance?.now?.() || Date.now();
            const response = await fetch("/api/stt", {
                signal: controller.signal,
                method: "POST",
                body: formData
            });

            if (!response.ok) {
                const errorPayload = await readErrorPayload(response, "这次没有顺利听清，我们再说一遍就好。");
                if (epoch !== voiceEpoch) return;
                const detail = applyVoiceError(errorPayload, "这次没有顺利听清，我们再说一遍就好。");
                finalizeTurnMetrics();
                setPhase("idle", "idle", "这次没有顺利听清", detail, "warning");
                scheduleRestore();
                return;
            }

            const data = await response.json();
            if (epoch !== voiceEpoch) return;
            const transcript = String(data?.text || "").trim();
            debugState.last_transcript = transcript;
            debugState.error_code = String(data?.error_code || "").trim();
            debugState.error_message = "";
            debugState.fallback_used = false;
            debugState.asr_provider = "openai";
            debugState.asr_model = "whisper-1";
            debugState.transcribe_error_code = String(data?.error_code || "").trim();
            debugState.transcribe_confidence = data?.confidence ?? null;
            applyVoiceDiagnosis("transcribe", data?.diagnosis);
            debugState.metrics.transcribe_latency_ms = Math.max(0, Math.round((window.performance?.now?.() || Date.now()) - sttStartedAt));
            renderDebugPanel();

            if (!transcript) {
                debugState.error_code = "VOICE_ASR_FAILED";
                debugState.error_message = "Transcript was empty after /voice/transcribe";
                debugState.transcribe_error_code = "VOICE_ASR_FAILED";
                debugState.final_status = "transcribe_failed";
                applyVoiceDiagnosis("transcribe", {
                    tags: ["asr_failed"],
                    primary_issue: "voice_asr_failed",
                    severity: "error",
                    human_summary: "The speech-to-text step finished without a usable transcript.",
                    suggested_next_step: "Retry the recording and inspect the ASR provider output."
                });
                finalizeTurnMetrics();
                setPhase("idle", "idle", "这次没有听清具体内容", "我们再说一遍就好。", "warning");
                scheduleRestore();
                emitDebugEvent("transcribe_empty");
                return;
            }

            resetInputToTranscript(transcript);
            debugState.user_text_sent_to_chat = transcript;
            setPhase("thinking", "sending_chat", "我正在想怎么回答你。", "我会尽量用简单一点的话回答。");
            emitDebugEvent("chat_request_start", transcript.slice(0, 36));

            if (typeof window.sendMessageFromVoice === "function") {
                const result = await window.sendMessageFromVoice(transcript, {
                    onSuccess(payload) {
                        debugState.metrics.chat_latency_ms = payload.latency_ms ?? null;
                        applyChatDiagnostics(payload.diagnostics);
                        renderDebugPanel();
                    },
                    onError(payload) {
                        debugState.metrics.chat_latency_ms = payload.latency_ms ?? null;
                        debugState.error_code = "CHAT_REQUEST_FAILED";
                        debugState.error_message = payload.error_message || "Chat request failed";
                        renderDebugPanel();
                    }
                });
                if (!result?.success) {
                    emitDebugEvent("chat_request_failed", result?.error_message || "unknown");
                }
            }
        } catch (error) {
            if (epoch !== voiceEpoch) return;
            console.error(error);
            debugState.error_code = "VOICE_UNKNOWN_ERROR";
            debugState.error_message = error instanceof Error ? error.message : "Unknown transcribe error";
            debugState.transcribe_error_code = "VOICE_UNKNOWN_ERROR";
            debugState.final_status = "transcribe_failed";
            applyVoiceDiagnosis("transcribe", {
                tags: ["asr_failed"],
                primary_issue: "voice_asr_failed",
                severity: "error",
                human_summary: "The ASR step did not complete cleanly.",
                suggested_next_step: "Inspect the recording payload and the transcribe-stage error details."
            });
            finalizeTurnMetrics();
            setPhase("idle", "idle", "这次没有顺利听清", "先继续文字聊天也可以。", "warning");
            scheduleRestore();
            emitDebugEvent("transcribe_exception", debugState.error_message);
        } finally {
            window.clearTimeout(timeout);
            if (sttController === controller) sttController = null;
        }
    }

    function stopListening(options = {}) {
        window.clearInterval(recordingTimer);
        recordingTimer = null;
        if (options.cancelPendingBlob) {
            discardNextRecording = true;
            recordedChunks = [];
        }

        if (mediaRecorder && mediaRecorder.state !== "inactive") {
            mediaRecorder.stop();
        }

        releaseStream();
        if (!options.keepStatus && currentState === "listening") {
            setPhase("thinking", "uploading_audio", "录音已结束，正在识别", "识别完成后会发送给陪伴助手。");
        }
    }

    async function startListening() {
        if (!hasRecorderSupport) {
            voiceButton.classList.add("is-unsupported");
            setPhase("idle", "idle", "当前设备暂不支持录音", "这台浏览器还不能直接录音，先继续打字也可以。", "warning");
            return;
        }

        const epoch = ++voiceEpoch;
        setPhase("thinking", "requesting_mic", "正在打开麦克风", "请在浏览器提示中允许使用麦克风；也可以停止后改用文字。");
        try {
            clearRestoreTimer();
            cleanupAudioPlayback();
            releaseStream();
            recordedChunks = [];
            resetTurnMetrics();
            turnStartedAt = window.performance?.now?.() || Date.now();

            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            if (epoch !== voiceEpoch) {
                stream.getTracks().forEach((track) => track.stop());
                return;
            }
            currentStream = stream;
            discardNextRecording = false;
            const mimeType = pickRecordingMimeType();
            mediaRecorder = mimeType
                ? new MediaRecorder(currentStream, { mimeType })
                : new MediaRecorder(currentStream);

            mediaRecorder.addEventListener("dataavailable", (event) => {
                if (epoch !== voiceEpoch) return;
                if (event.data && event.data.size > 0) {
                    recordedChunks.push(event.data);
                }
            });

            mediaRecorder.addEventListener("stop", async () => {
                if (epoch !== voiceEpoch) return;
                window.clearInterval(recordingTimer);
                const chunks = [...recordedChunks];
                const recorderMimeType = mediaRecorder?.mimeType || mimeType || "audio/webm";
                const shouldDiscard = discardNextRecording;
                debugState.metrics.record_duration_ms = recordStartedAt > 0
                    ? Math.max(0, Math.round((window.performance?.now?.() || Date.now()) - recordStartedAt))
                    : null;
                recordedChunks = [];
                discardNextRecording = false;
                mediaRecorder = null;
                recordStartedAt = 0;
                releaseStream();

                if (shouldDiscard) {
                    finalizeTurnMetrics();
                    setPhase("idle", "idle", "陪伴中", defaultHelpText);
                    emitDebugEvent("record_discarded");
                    return;
                }

                if (!chunks.length) {
                    debugState.error_code = "VOICE_AUDIO_EMPTY";
                    debugState.error_message = "No audio chunks recorded by MediaRecorder";
                    debugState.final_status = "record_empty";
                    applyVoiceDiagnosis("transcribe", {
                        tags: ["audio_empty", "asr_failed"],
                        primary_issue: "voice_asr_failed",
                        severity: "error",
                        human_summary: "The browser did not produce usable audio chunks for the turn.",
                        suggested_next_step: "Retry recording and confirm microphone capture is active."
                    });
                    finalizeTurnMetrics();
                    setPhase("idle", "idle", "这次没有录到声音", "再说一遍就好。", "warning");
                    scheduleRestore();
                    emitDebugEvent("record_empty");
                    return;
                }

                const audioBlob = new Blob(chunks, { type: recorderMimeType });
                await transcribeAndSend(audioBlob);
            });

            mediaRecorder.addEventListener("error", () => {
                if (epoch !== voiceEpoch) return;
                cancelVoice();
                setPhase("idle", "idle", "录音中断了", "请重试录音，或使用下方文字输入。", "warning");
            });

            mediaRecorder.start();
            recordStartedAt = window.performance?.now?.() || Date.now();
            setPhase("listening", "listening", "我在听你说", "说完后点「结束并发送」。每次最多录音 60 秒。", "");
            const timer = document.getElementById("recording-duration");
            if (timer) timer.textContent = "已录音 0 秒 / 60 秒";
            recordingTimer = window.setInterval(() => {
                const seconds = Math.floor(((window.performance?.now?.() || Date.now()) - recordStartedAt) / 1000);
                if (timer) timer.textContent = `已录音 ${seconds} 秒 / 60 秒`;
                if (seconds >= 60) stopListening();
            }, 1000);
            emitDebugEvent("record_start");
        } catch (error) {
            if (epoch !== voiceEpoch) return;
            console.error(error);
            releaseStream();
            mediaRecorder = null;
            recordedChunks = [];
            recordStartedAt = 0;
            debugState.error_code = "VOICE_UNKNOWN_ERROR";
            debugState.error_message = error instanceof Error ? error.message : "Microphone start failed";
            debugState.final_status = "record_start_failed";
            applyVoiceDiagnosis("transcribe", {
                tags: ["asr_failed"],
                primary_issue: "voice_asr_failed",
                severity: "error",
                human_summary: "The voice turn could not start because microphone capture failed.",
                suggested_next_step: "Check browser microphone permissions before retrying."
            });
            finalizeTurnMetrics();
            const detail = error.name === "NotAllowedError" ? "麦克风权限未开启。请在浏览器地址栏的权限设置中允许麦克风，或改用文字。"
                : error.name === "NotFoundError" ? "没有找到麦克风，请连接麦克风后重试，或改用文字。"
                    : "麦克风暂时无法使用，请检查是否被其他应用占用，或改用文字。";
            setPhase("idle", "idle", "这次没有顺利开始", detail, "warning");
            scheduleRestore();
            emitDebugEvent("record_start_failed", debugState.error_message);
        }
    }

    function cancelVoice() {
        if (currentStep === "sending_chat") {
            muteCurrentReply = true;
            stopSpeaking({ silent: true, preserveState: true });
            setPhase("thinking", "sending_chat", "仍在等待回复", "本次回复只显示文字，不会自动朗读。");
            return;
        }
        voiceEpoch += 1;
        sttController?.abort();
        sttController = null;
        stopListening({ keepStatus: true, cancelPendingBlob: true });
        mediaRecorder = null;
        stopSpeaking({ silent: true, preserveState: true });
        clearRestoreTimer();
        setPhase("idle", "idle", "已停止", defaultHelpText);
    }

    function toggleListening() {
        if (currentState === "thinking") {
            setHelpText("我还在回这句话，等一下就继续听你说。", "warning");
            renderStatusStrip();
            return;
        }

        if (currentState === "speaking") {
            stopSpeaking({ silent: true, preserveState: true, reason: "interrupt_to_record" });
            emitDebugEvent("playback_interrupted");
            startListening();
            return;
        }

        if (currentState === "listening") {
            emitDebugEvent("record_stop");
            stopListening();
            return;
        }

        startListening();
    }

    setHelpText(defaultHelpText);
    setPhase("idle", "idle", "陪伴中", defaultHelpText);
    if (ttsToggle) {
        ttsToggle.checked = readTtsEnabled();
        updateTtsFallbackStatus(ttsToggle.checked ? "收到回复后自动朗读" : "语音朗读已关闭");
        ttsToggle.addEventListener("change", () => {
            try { window.localStorage.setItem("conversation_tts_enabled", String(ttsToggle.checked)); } catch { /* Private browsing may disable storage. */ }
            updateTtsFallbackStatus(ttsToggle.checked ? "收到回复后自动朗读" : "语音朗读已关闭");
            if (!ttsToggle.checked) {
                const playing = currentState === "speaking" || currentStep === "generating_speech";
                stopSpeaking({ silent: true, preserveState: !playing });
            }
        });
    }
    if (debugPanel) {
        debugPanel.hidden = !debugEnabled;
    }
    if (copyDiagnosticsButton) {
        copyDiagnosticsButton.addEventListener("click", copyCurrentDiagnostics);
    }
    if (!hasRecorderSupport) {
        voiceButton.classList.add("is-unsupported");
    }

    voiceButton.addEventListener("click", toggleListening);
    stopSpeakingButton.addEventListener("click", () => {
        cancelVoice();
    });
    window.addEventListener("pagehide", () => {
        voiceEpoch += 1;
        sttController?.abort();
        stopListening({ keepStatus: true, cancelPendingBlob: true });
        stopSpeaking({ silent: true, preserveState: true });
        clearRestoreTimer();
    });

    window.ConversationVoice = {
        onThinking(meta = {}) {
            clearRestoreTimer();
            voiceEpoch += 1;
            sttController?.abort();
            stopListening({ keepStatus: true, cancelPendingBlob: true });
            muteCurrentReply = false;
            stopSpeaking({ silent: true, preserveState: true });
            const nextStep = "sending_chat";
            const nextText = meta.source === "voice" ? "我正在想怎么回答你。" : "我在想一下。";
            setPhase("thinking", nextStep, nextText, "我会尽量用简单一点的话回答。");
            emitDebugEvent("chat_thinking", meta.source || "text");
        },
        handleAssistantReply(reply, meta = {}) {
            if (meta.chatLatencyMs !== undefined) {
                debugState.metrics.chat_latency_ms = meta.chatLatencyMs;
            }
            debugState.assistant_reply = String(reply || "").trim();
            applyChatDiagnostics(meta.diagnostics);
            renderDebugPanel();
            requestSpeech(reply, meta);
        },
        onError(meta = {}) {
            if (currentState === "listening") {
                stopListening({ keepStatus: true, cancelPendingBlob: true });
            }
            stopSpeaking({ silent: true });
            if (meta.chatLatencyMs !== undefined) {
                debugState.metrics.chat_latency_ms = meta.chatLatencyMs;
            }
            if (meta.error) {
                debugState.error_message = String(meta.error);
            }
            debugState.final_status = "chat_failed";
            finalizeTurnMetrics();
            setPhase("idle", "idle", "暂时没有收到回复", "内容已留在输入框。可检查网络后重试；上一次请求可能已保存，请勿连续重试。", "warning");
            scheduleRestore();
            emitDebugEvent("chat_error", meta.error || meta.source || "unknown");
        },
        stopSpeaking() {
            stopSpeaking();
        },
        setIdle() {
            cancelVoice();
            if (currentStep === "sending_chat") return;
            finalizeTurnMetrics();
            setPhase("idle", "idle", "陪伴中", defaultHelpText);
        }
    };
})();

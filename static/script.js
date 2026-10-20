const bootstrap = window.APP_BOOTSTRAP || {};
const supportMeta = bootstrap.supportMeta || {
    value: "alzheimer",
    label: "阿尔兹海默症陪伴支持",
    description: "围绕熟悉的人、地方和往事慢慢展开，帮助陪伴与温和回忆。"
};

const activePage = document.body?.dataset.page || bootstrap.activePage || "dashboard";

let currentProfile = bootstrap.profile ? { ...bootstrap.profile } : {};
let currentSelectedPatient = bootstrap.selectedPatient ? { ...bootstrap.selectedPatient } : {};
let currentUserId = currentProfile.id || null;
let currentLogs = Array.isArray(bootstrap.recentLogs) ? [...bootstrap.recentLogs] : [];
let currentMemoryDigest = bootstrap.memoryDigest ? { ...bootstrap.memoryDigest } : {};
let currentReminders = Array.isArray(bootstrap.reminders) ? [...bootstrap.reminders] : [];
let currentEventLogs = Array.isArray(bootstrap.eventLogs) ? [...bootstrap.eventLogs] : [];
let currentCaregiverLinks = Array.isArray(bootstrap.caregiverLinks) ? [...bootstrap.caregiverLinks] : [];
let currentCareDigest = bootstrap.careDigest ? { ...bootstrap.careDigest } : {};
let currentCaregiverPatientId = bootstrap.caregiverPatientId || "demo_patient_001";
const chatSessionStorageKey = `alz-chat-session-${currentCaregiverPatientId}`;
let currentChatSessionId = sessionStorage.getItem(chatSessionStorageKey) || `${currentCaregiverPatientId}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
sessionStorage.setItem(chatSessionStorageKey, currentChatSessionId);
let currentCaregiverEvents = Array.isArray(bootstrap.caregiverEvents) ? [...bootstrap.caregiverEvents] : [];
let currentRiskEvents = [];
let currentCaregiverInsight = bootstrap.caregiverInsight ? { ...bootstrap.caregiverInsight } : {};
let currentDailyCareSummary = bootstrap.dailyCareSummary ? { ...bootstrap.dailyCareSummary } : {};
let currentDailyMoodSummary = {};
let currentMedicationSchedules = [];
let currentFamiliarMaterials = Array.isArray(bootstrap.familiarMaterials) ? [...bootstrap.familiarMaterials] : [];
let currentFamiliarMaterialStatus = bootstrap.familiarMaterialStatus ? { ...bootstrap.familiarMaterialStatus } : {};
let currentMemoryCandidates = Array.isArray(bootstrap.memoryCandidates) ? [...bootstrap.memoryCandidates] : [];
let openMemoryCandidateEditorId = null;
const memoryCandidateDrafts = new Map();
const reminiscenceEscortIds = new Set();
const reminiscenceCategories = ["家人", "往事", "爱好", "其他"];
let currentReminiscenceMemoriesByCategory = { "家人": [], "往事": [], "爱好": [], "其他": [] };
let currentReminiscenceSearchResults = [];
let currentReminiscenceAiTopics = [];
let currentSelectedReminiscenceMemoryId = null;
let reminiscenceSearchTimer = null;
let currentLastChatDiagnostics = null;
let currentLlmStatus = null;
let currentTestResults = null;
let editingReminderId = null;
let medicationReminderPollTimer = null;

function legacyProfileUserId() {
    const value = String(currentUserId || "").trim();
    return /^\d+$/.test(value) ? value : "";
}
let activeMedicationReminder = null;
const medicationSnoozeUntilById = new Map();
const shownMedicationReminderIds = new Set();
const debugMode = Boolean(bootstrap.debugMode) || new URLSearchParams(window.location.search).get("debug") === "1";

const sendButtonDefaultText = "发送";
const saveButtonDefaultText = "保存档案";
const defaultWelcomeMessage = "你好。想起谁了，或者想说哪件事，我们就从那里开始。";
const defaultConversationComposerNote = "点一下开始说话，说完再点一下结束并发送。文字输入可按 Enter 发送。";
const inputPlaceholder = "想起谁了？或者想说哪件事？";
const deviceToggleStorageKey = "alz-device-settings";

const reminderTypeLabels = {
    medication: "用药提醒",
    meal: "用餐提醒",
    phone_call: "电话提醒",
    sleep: "睡前提醒",
    custom: "自定义提醒",
    medicine: "吃药提醒",
    water: "喝水提醒",
    routine: "作息提醒",
    activity: "活动 / 散步提醒",
    later: "稍后提醒一次"
};

const reminderStatusLabels = {
    pending: "待确认",
    reminded: "已提醒",
    confirmed: "已确认",
    missed: "未完成",
    skipped: "已跳过"
};

const eventTypeLabels = {
    agitation: "情绪激越",
    medication_refusal: "拒药",
    nighttime: "夜间异常",
    wandering_risk: "离家倾向",
    sleep: "睡眠异常",
    repeated_question: "重复提问",
    medication_uncertainty: "用药不确定",
    anxiety: "焦虑/害怕",
    wandering_intent: "外出风险",
    disorientation: "位置困惑",
    reminiscence_need: "人物回忆需要",
    sensitive_deceased_spouse: "已故亲人话题",
    sensitive_deceased_spouse_topic: "已故亲人话题",
    date_time_confusion: "日期时间困惑",
    person_recognition: "人物识别困难",
    suspicion_or_delusion: "疑似被偷妄想",
    safety_check: "安全确认",
    other: "其他事件"
};

const severityLabels = {
    low: "低",
    medium: "中",
    high: "高"
};

const materialTypeLabels = {
    family_photo: "家人照片",
    voice_message: "语音留言",
    familiar_music: "熟悉音乐",
    old_place: "旧地点",
    old_event: "旧事件",
    daily_object: "日常物品",
    sensitive_memory: "敏感记忆"
};

let materialVoiceRecorder = null;
let materialVoiceChunks = [];
let materialVoiceStopTimer = null;
let materialVoiceRecordingId = null;

const chatHistoryCategoryLabels = {
    normal: "普通聊天",
    repeated_question: "重复提问",
    medication_uncertainty: "用药不确定",
    anxiety: "焦虑/害怕",
    disorientation: "位置困惑",
    wandering_intent: "外出风险",
    sensitive_deceased_spouse_topic: "敏感亲人话题",
    reminiscence_content: "回忆内容"
};

const chatHistoryDetectedStateLabels = {
    normal: "日常交流",
    repeated_question: "重复提问",
    medication_uncertainty: "用药确认",
    anxiety: "情绪安抚",
    disorientation: "位置困惑",
    wandering_intent: "外出风险",
    sensitive_deceased_spouse_topic: "敏感亲人话题",
    reminiscence_content: "回忆线索"
};

const chatHistoryStrategyLabels = {
    normal: "温和回应",
    repeated_question: "重复安抚",
    medication_uncertainty: "提醒核对",
    anxiety: "低刺激安抚",
    disorientation: "定向安抚",
    wandering_intent: "陪伴转移",
    sensitive_deceased_spouse_topic: "敏感模板",
    reminiscence_content: "回忆引导"
};

const materialTypeFormHints = {
    family_photo: {
        helper: "家人照片建议填写图片链接、缩略图、关联人物，方便患者端人物识别和熟悉感建立。",
        filePath: "例如：https://example.com/xiaoyu-photo.jpg",
        thumbnail: "例如：https://example.com/xiaoyu-thumb.jpg",
        transcript: "可选：补充照片里的场景说明",
        artist: "家人照片一般可留空",
        useScene: "例如：person_recognition / reminiscence"
    },
    voice_message: {
        helper: "语音留言建议填写音频链接和 transcript_text，方便系统在焦虑、重复提问时生成更熟悉的安抚回复。",
        filePath: "例如：https://example.com/xiaoyu-voice.mp3",
        thumbnail: "可选：语音封面或家人头像",
        transcript: "例如：妈妈别担心，我晚上 8 点会联系你。",
        artist: "语音留言一般可留空",
        useScene: "例如：anxiety / repeated_question / good_night"
    },
    familiar_music: {
        helper: "熟悉音乐可填写 music_url、artist 和 use_scene，用于轻柔转移注意力或陪伴。",
        filePath: "例如：https://example.com/playlist/molihua",
        thumbnail: "可选：专辑封面",
        transcript: "可选：歌词摘要或推荐原因",
        artist: "例如：邓丽君",
        useScene: "例如：afternoon_anxiety / reminiscence / sleep"
    },
    old_place: {
        helper: "旧地点建议写清地点描述、相关时间和关联人物，帮助系统做低刺激回忆引导。",
        filePath: "例如：照片路径、地图链接或留空",
        thumbnail: "可选：旧地点照片",
        transcript: "可选：地点相关的小故事",
        artist: "旧地点一般可留空",
        useScene: "例如：reminiscence / orientation"
    },
    old_event: {
        helper: "旧事件建议写清相关时间、人物和简短描述，便于系统用熟悉经历接话。",
        filePath: "可选：事件照片、录音或留空",
        thumbnail: "可选：事件相关图片",
        transcript: "可选：事件摘要",
        artist: "旧事件一般可留空",
        useScene: "例如：reminiscence / life_story"
    },
    daily_object: {
        helper: "日常物品可帮助患者围绕熟悉物件展开对话，适合填写照片、用途和使用场景。",
        filePath: "例如：药盒、收音机、围裙的图片链接",
        thumbnail: "可选：物品缩略图",
        transcript: "可选：物品相关说明",
        artist: "日常物品一般可留空",
        useScene: "例如：daily_routine / conversation_anchor"
    },
    sensitive_memory: {
        helper: "敏感记忆必须填写 safety_note。系统不会主动刺激患者，只有相关话题触发时才用于安全模板。",
        filePath: "可选：仅供家属留存的内部链接",
        thumbnail: "敏感素材一般不建议使用强刺激缩略图",
        transcript: "可选：只写给家属看的简短摘要",
        artist: "敏感记忆一般可留空",
        useScene: "例如：sensitive_topic / emotional_support"
    }
};


document.addEventListener("DOMContentLoaded", async () => {
    updateSupportCopy();
    bindPageEvents();
    initializeConversationLayout();
    renderAll();
    if (isPage("conversation")) {
        window.setInterval(renderConversationTopStatus, 60 * 1000);
        hydrateConversationModelStatus();
        hydrateSeedMessage();
    }
    await hydratePageState();
    if (isPage("dashboard")) {
        startMedicationReminderPolling();
    }
});


function element(id) {
    return document.getElementById(id);
}


function hydrateSeedMessage() {
    const seedMessage = new URLSearchParams(window.location.search).get("seed_message");
    const input = element("input");
    if (seedMessage && input) {
        input.value = seedMessage;
        updateComposerNote("已带入回忆素材，可以直接发送。");
    }
}


function isPage(name) {
    return activePage === name;
}


function hasProfileForm() {
    return Boolean(
        element("profile-id")
        && element("name")
        && element("age")
        && element("hometown")
        && element("family-info")
        && element("life-events")
        && element("preferences")
        && element("notes")
    );
}


function bindPageEvents() {
    const input = element("input");
    const sendButton = element("send-button");
    const saveButton = element("save-button");
    const trackedFields = [
        "name",
        "age",
        "hometown",
        "family-info",
        "life-events",
        "preferences",
        "notes"
    ];

    if (isPage("conversation") && input) {
        input.addEventListener("keydown", (event) => {
            if (event.key === "Enter" && !event.shiftKey && !event.isComposing && event.keyCode !== 229) {
                event.preventDefault();
                sendMessage();
            }
        });

        input.addEventListener("input", () => {
            updateComposerNote(defaultConversationComposerNote);
        });
    }

    if (isPage("conversation") && sendButton) {
        sendButton.addEventListener("click", sendMessage);
    }

    if (isPage("conversation")) {
        document.querySelectorAll(".conversation-quick-test").forEach((button) => {
            button.addEventListener("click", () => {
                if (input) {
                    input.value = button.dataset.message || "";
                    input.focus();
                }
                sendMessage();
            });
        });
    }

    if (isPage("profile") && saveButton) {
        saveButton.addEventListener("click", () => {
            saveProfile();
        });
        bindCaregiverForm();
    }

    if (isPage("device")) {
        bindDeviceToggle("meal-toggle", "meal");
        bindDeviceToggle("water-toggle", "water");
        bindDeviceToggle("medicine-toggle", "medicine");
        bindDeviceToggle("rest-toggle", "rest");
        bindDeviceToggle("autoplay-toggle", "autoplay");
        bindDeviceSelect("speech-length-select", "speechLength");
        bindDeviceSelect("speech-rhythm-select", "speechRhythm");
        bindReminderCenter();
    }

    if (isPage("dashboard")) {
        bindMedicationScheduleSettings();
        element("dashboard-record-today-button")?.addEventListener("click", recordTodayFromDashboard);
    }

    if (isPage("safety")) {
        const wanderingButton = element("wandering-event-button");
        if (wanderingButton) {
            wanderingButton.addEventListener("click", () => {
                createEventLog({
                    event_type: "wandering_risk",
                    severity: "medium",
                    description: "家属记录了一次离家倾向或位置安全相关事件。",
                    source: "location_safety",
                    created_by: "family"
                });
            });
        }
    }

    if (isPage("notes")) {
        bindEventLogForm();
    }

    if (isPage("materials")) {
        bindMaterialsPage();
    }

    if (!isPage("profile")) {
        return;
    }

    trackedFields.forEach((fieldId) => {
        const field = element(fieldId);
        if (!field) {
            return;
        }

        field.addEventListener("input", () => {
            updateProfileStatus("档案内容已变更，确认后保存即可。", "warning");
            currentProfile = getCurrentProfileSnapshot();
            renderSummaryPanels(currentProfile, currentLogs);
            renderDashboardProfileCard(currentProfile);
        });
    });
}


function renderAll() {
    const profile = getCurrentProfileSnapshot();

    if (isPage("conversation")) {
        renderConversationPatientHeader(profile);
        renderConversationTopStatus();
        updateConversationLayout();
        renderInitialMessages(currentLogs);
        return;
    }

    if (isPage("profile")) {
        updateProfileStatus("档案已载入，可继续补充或修订。");
        fillProfileForm(profile);
        renderCaregiverLinks("caregiver-link-list", currentCaregiverLinks);
        return;
    }

    if (isPage("dashboard")) {
        renderSummaryPanels(profile, currentLogs);
        renderDashboardProfileCard(profile);
        renderDashboardMoodCard();
        renderDashboardCarePolish();
        renderMedicationScheduleSettings();
        return;
    }

    if (isPage("notes")) {
        renderSummaryPanels(profile, currentLogs);
        renderEventLogList("event-log-list", currentEventLogs);
        renderLogList("notes-log-list", currentLogs);
        return;
    }

    if (isPage("analysis")) {
        renderSummaryPanels(profile, currentLogs);
        renderCaregiverInsight();
        renderDailyCareLoop();
        renderAnalysisReminderTasks();
        renderRecentChatSummary();
        renderMaterialStatusSummary();
        renderMemoryCandidateStatusSummary();
        renderCaregiverEventDetails();
        renderAnalysisCurrentDate();
        setTextIfPresent("analysis-recent-chat-summary", buildRecentTopicsSummary(profile, currentLogs));
        return;
    }

    if (isPage("debug_dashboard")) {
        renderDebugDashboard();
        return;
    }

    if (isPage("test_results")) {
        renderTestResults();
        return;
    }

    if (isPage("materials")) {
        renderMaterialsPage();
        return;
    }

    if (isPage("chat_history")) {
        renderChatHistoryPage();
        return;
    }

    if (isPage("reminiscence")) {
        renderReminiscencePage();
        return;
    }

    if (isPage("device")) {
        renderDeviceSettings();
        renderReminderList("reminder-list", currentReminders);
    }

    if (isPage("safety")) {
        renderSummaryPanels(profile, currentLogs);
    }
}


async function hydratePageState() {
    await loadProfile();
    await loadRecentChatLogs();
    await loadCareData();
    if (isPage("dashboard")) {
        await loadMedicationSchedules();
    }
    if (isPage("materials") || isPage("analysis") || isPage("chat_history") || isPage("reminiscence")) {
        await loadFamiliarMaterials();
    }
    if (isPage("reminiscence")) {
        await loadReminiscenceMemories();
        await loadReminiscenceAiTopics();
    }
    if (isPage("chat_history") || isPage("analysis")) {
        await loadMemoryCandidates();
    }
    if (isPage("debug_dashboard")) {
        await hydrateDebugDashboard();
    }
    if (isPage("test_results")) {
        await hydrateTestResults();
    }
}


function getCurrentMode() {
    return supportMeta.value || "alzheimer";
}


function updateSupportCopy() {
    document.body.dataset.mode = "alzheimer";

    const input = element("input");

    if (input) {
        input.placeholder = inputPlaceholder;
    }
}


function getCurrentProfileSnapshot() {
    if (!hasProfileForm()) {
        return { ...currentProfile };
    }

    const ageValue = element("age").value.trim();
    const idValue = element("profile-id").value.trim();
    const age = ageValue ? parseInt(ageValue, 10) : null;

    return {
        ...currentProfile,
        id: idValue ? parseInt(idValue, 10) : currentProfile.id || null,
        name: element("name").value.trim(),
        age: Number.isNaN(age) ? null : age,
        hometown: element("hometown").value.trim(),
        support_mode: getCurrentMode(),
        family_info: element("family-info").value.trim(),
        life_events: element("life-events").value.trim(),
        preferences: element("preferences").value.trim(),
        notes: element("notes").value.trim()
    };
}


function cleanPieces(text) {
    return String(text || "")
        .split(/[，,；;。！!？?\n]/)
        .map((part) => part.trim())
        .filter(Boolean);
}


function shortText(text, maxLength = 30) {
    const value = String(text || "").trim();
    if (value.length <= maxLength) {
        return value;
    }
    return `${value.slice(0, maxLength)}...`;
}


function formatDateKey(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
}


function formatLocalTimestamp(date = new Date()) {
    const hours = String(date.getHours()).padStart(2, "0");
    const minutes = String(date.getMinutes()).padStart(2, "0");
    const seconds = String(date.getSeconds()).padStart(2, "0");
    return `${formatDateKey(date)}T${hours}:${minutes}:${seconds}`;
}


function formatDisplayTime(timestamp) {
    const value = String(timestamp || "");
    if (!value) {
        return "";
    }
    const parts = value.split("T");
    return parts[1] ? parts[1].slice(0, 5) : value;
}


function formatConversationDate(date = new Date()) {
    const weekdays = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"];
    const month = date.getMonth() + 1;
    const day = date.getDate();
    return `${month}月${day}日 ${weekdays[date.getDay()]}`;
}


function renderConversationTopStatus() {
    if (!isPage("conversation")) {
        return;
    }

    const dateText = element("device-date-text");
    const timeText = element("device-time-text");
    const now = new Date();

    if (dateText) {
        dateText.textContent = formatConversationDate(now);
    }
    if (timeText) {
        timeText.textContent = formatDisplayTime(formatLocalTimestamp(now)) || "";
    }
}


function getConversationElements() {
    return {
        chatBox: element("chat-box"),
        controlDock: document.querySelector(".device-control-dock"),
        conversationShell: document.querySelector(".conversation-device-shell")
    };
}


function ensureConversationScrollAnchor(chatBox) {
    if (!chatBox) {
        return null;
    }

    let anchor = chatBox.querySelector(".conversation-scroll-anchor");
    if (anchor instanceof HTMLElement) {
        return anchor;
    }

    anchor = document.createElement("div");
    anchor.className = "conversation-scroll-anchor";
    anchor.setAttribute("aria-hidden", "true");
    chatBox.appendChild(anchor);
    return anchor;
}


function updateConversationLayout() {
    if (!isPage("conversation")) {
        return;
    }

    const { chatBox, controlDock, conversationShell } = getConversationElements();
    if (!chatBox || !controlDock || !conversationShell) {
        return;
    }

    const dockHeight = Math.ceil(controlDock.getBoundingClientRect().height);
    const safeGap = window.innerWidth <= 768 ? 22 : 28;
    const visibleBottomSpace = safeGap + 16;
    const anchor = ensureConversationScrollAnchor(chatBox);

    conversationShell.style.setProperty("--conversation-dock-height", `${dockHeight}px`);
    conversationShell.style.setProperty("--conversation-safe-space", `${visibleBottomSpace}px`);
    chatBox.style.scrollPaddingBottom = `${visibleBottomSpace}px`;

    if (anchor) {
        anchor.style.height = `${visibleBottomSpace}px`;
    }
}


function scrollConversationToLatest(options = {}) {
    if (!isPage("conversation")) {
        return;
    }

    const { immediate = false } = options;
    const { chatBox } = getConversationElements();
    if (!chatBox) {
        return;
    }

    const performScroll = () => {
        const visibleBottomOffset = Math.max(0, chatBox.scrollHeight - chatBox.clientHeight);
        chatBox.scrollTop = visibleBottomOffset;
    };

    window.requestAnimationFrame(() => {
        performScroll();
        window.requestAnimationFrame(performScroll);
    });
}


function initializeConversationLayout() {
    if (!isPage("conversation")) {
        return;
    }

    const { controlDock } = getConversationElements();
    updateConversationLayout();

    window.addEventListener("resize", () => {
        updateConversationLayout();
        scrollConversationToLatest({ immediate: true });
    });

    if (controlDock && "ResizeObserver" in window) {
        const dockObserver = new ResizeObserver(() => {
            updateConversationLayout();
            scrollConversationToLatest({ immediate: true });
        });
        dockObserver.observe(controlDock);
    }
}


function providerDisplayName(provider) {
    const normalized = String(provider || "").toLowerCase();
    return {
        deepseek: "DeepSeek",
        minimax: "MiniMax",
        zhipu: "Zhipu",
        openai: "OpenAI",
        mock: "Mock",
        template_fallback: "Template fallback"
    }[normalized] || (provider || "未知");
}


function yesNo(value) {
    return value ? "是" : "否";
}


function compactDebugText(text, maxLength = 300) {
    const value = String(text || "").trim();
    if (!value) {
        return "暂无";
    }
    return value.length > maxLength ? `${value.slice(0, maxLength)}...` : value;
}


async function hydrateConversationModelStatus() {
    if (!isPage("conversation")) {
        return;
    }
    try {
        const [statusResponse, lastChatResponse] = await Promise.all([
            fetch("/api/debug/llm-status"),
            fetch("/api/debug/last-chat")
        ]);
        if (statusResponse.ok) {
            currentLlmStatus = await statusResponse.json();
        }
        if (lastChatResponse.ok) {
            const payload = await lastChatResponse.json();
            currentLastChatDiagnostics = payload.diagnostics || null;
        }
    } catch (error) {
        console.warn("[debug] model status unavailable", error);
    }
    renderConversationModelStatus(currentLastChatDiagnostics, currentLlmStatus);
}


function renderConversationModelStatus(diagnostics = null, status = null) {
    if (!isPage("conversation")) {
        return;
    }
    const diag = diagnostics || currentLastChatDiagnostics || {};
    const llmStatus = status || currentLlmStatus || {};
    const provider = diag.actual_provider || diag.provider || llmStatus.provider || "unknown";
    const requestedProvider = diag.requested_provider || llmStatus.provider || provider;
    const model = diag.model || llmStatus.model || "-";
    const requestedModel = diag.requested_model || model || llmStatus.model || "-";
    const apiKeyConfigured = Object.prototype.hasOwnProperty.call(diag, "api_key_configured")
        ? Boolean(diag.api_key_configured)
        : Boolean(llmStatus.api_key_configured);
    const fallbackUsed = Boolean(diag.fallback_used);
    const postprocessUsed = Boolean(diag.postprocess_used);
    const isTemplateFallback = provider === "template_fallback" || Boolean(diag.template_used);
    const displayProvider = isTemplateFallback ? "Template fallback" : fallbackUsed ? "Mock fallback" : providerDisplayName(provider);
    const apiState = isTemplateFallback ? "安全模板" : fallbackUsed ? "Fallback" : provider === "mock" ? "Mock/debug" : "真实 API";
    const requestedText = `${providerDisplayName(requestedProvider)} · ${requestedModel || "-"}`;
    const keyWarning = !apiKeyConfigured && requestedProvider === "deepseek"
        ? "DeepSeek API key 未读取，请检查 .env"
        : "";

    setTextIfPresent(
        "conversation-model-status-line",
        (fallbackUsed || isTemplateFallback) ? `当前模型：${displayProvider} · 原始请求 ${requestedText}` : `当前模型：${displayProvider} · ${model || "-"}`
    );
    setTextIfPresent("conversation-provider-hint", `当前模型：${displayProvider} · ${apiState}`);
    setTextIfPresent("conversation-model-provider", `${displayProvider} · ${apiState}`);
    setTextIfPresent("conversation-model-name", model || "-");
    setTextIfPresent("conversation-model-requested", requestedText);
    setTextIfPresent("conversation-model-fallback", yesNo(fallbackUsed));
    setTextIfPresent("conversation-model-postprocess", yesNo(postprocessUsed));
    setTextIfPresent(
        "conversation-model-strategy",
        [yesNo(Boolean(diag.template_used)), diag.detected_state || diag.strategy || "-"].join(" / ")
    );
    setTextIfPresent("conversation-model-latency", diag.response_time_ms ? `${diag.response_time_ms} ms` : "-");
    setTextIfPresent(
        "conversation-debug-reason",
        [
            keyWarning,
            diag.fallback_reason,
            diag.guard_reason,
            diag.template_name ? `template=${diag.template_name}` : "",
            `context_items=${diag.context_items_count ?? 0}`,
            `history_turns=${diag.history_turns_used ?? 0}`,
            `materials=${Array.isArray(diag.materials_used) ? diag.materials_used.length : 0}`,
            diag.reminder_status?.status ? `reminder_status=${diag.reminder_status.status}` : "",
            diag.material_match_reason || ""
        ].filter(Boolean).join(" / ") || "暂无"
    );
    setTextIfPresent("conversation-debug-context-count", String(diag.context_items_count ?? "-"));
    setTextIfPresent(
        "conversation-debug-materials",
        Array.isArray(diag.materials_used) && diag.materials_used.length
            ? diag.materials_used.map((item) => item.title || item.material_type || "material").join("，")
            : "无"
    );
    setTextIfPresent(
        "conversation-debug-reminder",
        diag.reminder_status?.status
            ? `${diag.reminder_status.status} · ${diag.reminder_status.title || ""}`.trim()
            : "无"
    );
    setTextIfPresent(
        "conversation-debug-caregiver",
        `caregiver_events_created=${diag.caregiver_events_created ?? 0}，reminder_events_created=${diag.reminder_events_created ?? 0}`
    );
}


function uniqueItems(items, limit = 3) {
    const seen = new Set();
    const result = [];

    items.forEach((item) => {
        const value = String(item || "").trim();
        if (!value || seen.has(value)) {
            return;
        }
        seen.add(value);
        result.push(value);
    });

    return result.slice(0, limit);
}


function getRecentUserMessages(logs, limit = 3) {
    return logs
        .filter((log) => log.role === "user" && log.message)
        .map((log) => String(log.message).trim())
        .filter(Boolean)
        .slice(-limit);
}


function extractTopicTags(logs, limit = 3) {
    const genericWords = new Set([
        "我们",
        "现在",
        "刚刚",
        "事情",
        "内容",
        "感觉",
        "方式",
        "聊天",
        "这句话",
        "可以",
        "一起"
    ]);

    const tagSource = logs.flatMap((log) => cleanPieces(log.keyword_tags || ""));
    const messageSource = getRecentUserMessages(logs, 5).flatMap((message) => cleanPieces(message));
    const merged = [...tagSource, ...messageSource]
        .map((item) => shortText(item, 12))
        .filter((item) => item.length >= 2 && !genericWords.has(item));

    return uniqueItems(merged, limit);
}


function includesHint(text, hints) {
    const normalized = String(text || "").trim();
    return hints.some((hint) => normalized.includes(hint));
}


function buildMemoryDigest(profile, logs) {
    const relationHints = ["女儿", "儿子", "妈妈", "爸爸", "老伴", "丈夫", "爱人", "家人", "姐姐", "哥哥", "妹妹", "弟弟"];
    const lifeHints = ["以前", "过去", "经历", "工作", "年轻", "小时候", "上班", "学校", "商场", "夫子庙"];
    const preferenceHints = ["喜欢", "爱好", "想听", "想吃", "偏好", "评弹", "老歌", "散步"];
    const placeHints = ["家乡", "老家", "南京", "上海", "杭州", "苏州", "地方", "住"];
    const logPieces = logs
        .filter((log) => log.role === "user")
        .flatMap((log) => [...cleanPieces(log.message || ""), ...cleanPieces(log.keyword_tags || "")]);
    const repeatedPieces = logs
        .filter((log) => log.role === "user" && Boolean(log.repeated_flag))
        .flatMap((log) => [...cleanPieces(log.keyword_tags || ""), ...cleanPieces(log.message || "")]);

    const mentionedPeople = uniqueItems(
        [
            ...logPieces.filter((piece) => includesHint(piece, relationHints)),
            ...cleanPieces(profile.family_info || "")
        ],
        3,
    );
    const lifeTopics = uniqueItems(
        [
            ...logPieces.filter((piece) => includesHint(piece, lifeHints)),
            ...cleanPieces(profile.life_events || "")
        ],
        3,
    );
    const preferenceTopics = uniqueItems(
        [
            ...logPieces.filter((piece) => includesHint(piece, preferenceHints)),
            ...cleanPieces(profile.preferences || "")
        ],
        3,
    );
    const placeTopics = uniqueItems(
        [
            ...logPieces.filter((piece) => includesHint(piece, placeHints)),
            ...(profile.hometown ? [profile.hometown] : []),
            ...cleanPieces(profile.notes || "")
        ],
        2,
    );
    const repeatedTopics = uniqueItems(repeatedPieces, 2);
    const followUpTopics = uniqueItems(
        [
            ...mentionedPeople,
            ...placeTopics,
            ...lifeTopics,
            ...preferenceTopics
        ],
        3,
    );

    const summaryParts = [];
    if (mentionedPeople.length) {
        summaryParts.push(`常提到的人有${mentionedPeople.join("、")}`);
    }
    if (placeTopics.length) {
        summaryParts.push(`熟悉地点会回到${placeTopics.join("、")}`);
    }
    if (lifeTopics.length) {
        summaryParts.push(`常聊经历有${lifeTopics.join("、")}`);
    }
    if (preferenceTopics.length) {
        summaryParts.push(`偏好线索里有${preferenceTopics.join("、")}`);
    }
    if (repeatedTopics.length) {
        summaryParts.push(`重复会回到${repeatedTopics.join("、")}`);
    }

    return {
        mentionedPeople,
        lifeTopics,
        preferenceTopics,
        placeTopics,
        repeatedTopics,
        followUpTopics,
        summary: summaryParts.length
            ? `${summaryParts.slice(0, 3).join("；")}。`
            : "现在还没有足够的历史内容，先从熟悉的人和旧日线索慢慢积累。"
    };
}


function buildRememberedPreferences(profile) {
    const rememberedParts = [];

    if (profile.preferences) {
        rememberedParts.push(`我记得这些会让 ta 更放松：${shortText(profile.preferences, 42)}。`);
    }
    if (profile.notes) {
        rememberedParts.push(`和 ta 相处时，我会留意：${shortText(profile.notes, 36)}。`);
    }
    if (!profile.preferences && profile.family_info) {
        rememberedParts.push(`我也记得 ta 身边重要的人：${shortText(profile.family_info, 36)}。`);
    }
    if (!profile.preferences && !profile.notes && profile.life_events) {
        rememberedParts.push(`我会带着这些熟悉经历陪 ta 聊：${shortText(profile.life_events, 36)}。`);
    }

    if (!rememberedParts.length) {
        return "你还没写下太多资料也没关系，我会先从你愿意说出的第一句话开始，慢慢记住真正重要的线索。";
    }

    return rememberedParts.slice(0, 2).join("");
}


function buildRecentTopicsSummary(profile, logs) {
    const memoryDigest = buildMemoryDigest(profile, logs);
    const userMessages = getRecentUserMessages(logs, 3);

    if (userMessages.length) {
        return `最近我们聊到过：${userMessages.map((message) => `“${shortText(message, 20)}”`).join("、")}。`;
    }

    if (memoryDigest.summary) {
        return memoryDigest.summary;
    }

    if (profile.family_info || profile.life_events || profile.preferences) {
        return "我们还没正式聊开，不过我已经记住了一些熟悉线索，随时可以从家人、经历或让人安心的小偏好开始。";
    }

    return "我们还没正式聊开，不过已经准备好接住下一句。";
}


function getLogsWithinDays(logs, days = 7) {
    const boundary = new Date();
    boundary.setHours(0, 0, 0, 0);
    boundary.setDate(boundary.getDate() - Math.max(days - 1, 0));

    return logs.filter((log) => {
        const timestamp = String(log.timestamp || "");
        if (!timestamp) {
            return false;
        }
        const date = new Date(timestamp);
        return !Number.isNaN(date.getTime()) && date >= boundary;
    });
}


function buildStuckPointsSummary(profile, logs) {
    const digest = buildMemoryDigest(profile, logs);
    const recentUsers = getRecentUserMessages(logs, 5);
    const clarificationCount = recentUsers.filter((message) => includesHint(message, ["什么", "听不清", "你再说", "没听懂", "那是谁"])).length;
    const shortReplyCount = recentUsers.filter((message) => String(message).trim().length <= 3).length;

    if (digest.repeatedTopics.length) {
        return `最近更容易卡在 ${digest.repeatedTopics.join("、")} 这些点上，陪伴时适合先短答，再顺着熟悉线索接。`;
    }

    if (clarificationCount >= 1) {
        return "最近更容易卡在“没听清”或“想确认上一句”的时刻，回应时最好先把上一句说得更短更清楚。";
    }

    if (shortReplyCount >= 2) {
        return "最近更容易停在短句回应上，可以优先从熟悉的人、地点或旧经历慢慢带开话题。";
    }

    if (digest.followUpTopics.length) {
        return `目前没有固定卡点，整体仍以 ${digest.followUpTopics.join("、")} 这些熟悉线索更容易接上。`;
    }

    return "目前还没有明显卡住的固定点，可以继续观察熟悉话题和回应节奏。";
}


function buildWeeklyInteractionSummary(logs) {
    const weeklyLogs = getLogsWithinDays(logs, 7);
    const userCount = weeklyLogs.filter((log) => log.role === "user").length;
    const assistantCount = weeklyLogs.filter((log) => log.role === "assistant").length;
    const activeDays = uniqueItems(weeklyLogs.map((log) => String(log.timestamp || "").slice(0, 10)), 7).length;

    if (!weeklyLogs.length) {
        return "本周还没有新的互动记录。";
    }

    if (!assistantCount) {
        return `本周已记录 ${userCount} 条用户输入，正在等待更多完整对话形成稳定判断。`;
    }

    return `本周共记录 ${assistantCount} 轮对话，分布在 ${Math.max(activeDays, 1)} 天，整体保持轻量互动节奏。`;
}


function buildSensitiveTopicsSummary(profile, logs) {
    const digest = buildMemoryDigest(profile, logs);
    const recentUsers = getRecentUserMessages(logs, 6);
    const uneasyMessages = recentUsers.filter((message) => includesHint(message, ["不对", "搞笑", "什么", "听不清", "我忘了", "不知道", "你再说"]));

    if (uneasyMessages.length) {
        return `最近更容易在“${shortText(uneasyMessages[uneasyMessages.length - 1], 12)}”这类时刻出现卡顿，建议先短答澄清，再回到熟悉线索。`;
    }

    if (digest.repeatedTopics.length) {
        return `当前更需要留意 ${digest.repeatedTopics.join("、")} 这些重复回到的话题，避免一次推太多信息。`;
    }

    return "目前没有特别突出的不安话题，仍建议保持短句、清楚、不过度追问。";
}


function buildFollowUpTopicText(profile, logs) {
    const digest = buildMemoryDigest(profile, logs);
    if (digest.followUpTopics.length) {
        return `更容易接上的仍是：${digest.followUpTopics.join("、")}。`;
    }
    if (digest.lifeTopics.length || digest.preferenceTopics.length) {
        return "更容易接上的通常是熟悉的人、旧经历和喜欢的事情。";
    }
    return "还需要更多互动记录，才能看出更稳定的承接话题。";
}


function buildCompanionStyleText() {
    return "我会围绕熟悉的人、地方和往事，陪 ta 把话慢慢说开。";
}


function extractMentionedItems(profile, logs, limit = 4) {
    const digest = buildMemoryDigest(profile, logs);
    return uniqueItems(
        [...digest.mentionedPeople, ...digest.lifeTopics, ...digest.preferenceTopics].map((item) => shortText(item, 18)),
        limit,
    );
}


function buildNotesGentleSummary(profile, logs) {
    const digest = buildMemoryDigest(profile, logs);
    if (!logs.length) {
        if (profile.family_info || profile.life_events || profile.preferences || profile.notes) {
            return "我们还没正式聊开，不过我已经带着这些熟悉线索在这里，随时可以从更安心的话题慢慢开始。";
        }

        return "现在还没有太多聊天内容，我会先带着已有资料，安静地准备好下一次陪伴。";
    }

    if (digest.summary) {
        return `最近更容易接住的线索是：${digest.summary}`;
    }

    return "最近已经有一些聊天内容了，我会继续沿着熟悉的人和往事，把陪伴保持得更稳定一点。";
}


function buildFollowUpSummary(profile, logs) {
    const digest = buildMemoryDigest(profile, logs);
    if (digest.followUpTopics.length) {
        return `最近更容易顺着聊下去的是：${digest.followUpTopics.join("、")}。`;
    }

    if (digest.lifeTopics.length || digest.preferenceTopics.length) {
        return "最近更容易接上的，还是熟悉的人、旧日经历和让人放松的小偏好。";
    }

    return "等再多聊几句，这里会慢慢出现更容易继续接下去的话题。";
}


function getRepeatedQuestionCount(logs) {
    return logs.filter((log) => log.role === "user" && Boolean(log.repeated_flag)).length;
}


function getConversationTurnCount(logs) {
    return logs.filter((log) => log.role === "assistant").length;
}


function buildRecentActivityText(logs) {
    if (!logs.length) {
        return "刚开始";
    }

    const latestLog = logs[logs.length - 1];
    return latestLog.timestamp ? `${String(latestLog.timestamp).slice(5, 16).replace("T", " ")}` : "刚刚互动";
}


function buildRepeatSummary(logs) {
    const repeatedCount = getRepeatedQuestionCount(logs);
    const repeatedItems = uniqueItems(
        logs
            .filter((log) => log.role === "user" && Boolean(log.repeated_flag))
            .flatMap((log) => [...cleanPieces(log.keyword_tags || ""), ...cleanPieces(log.message || "")]),
        2,
    );

    if (!repeatedCount) {
        return "当前还没有明显的重复提问记录。";
    }

    if (repeatedItems.length) {
        return `最近记录里有 ${repeatedCount} 次重复提问，主要会回到 ${repeatedItems.join("、")} 这些主题。`;
    }

    return `最近记录里有 ${repeatedCount} 次重复提问，后续陪伴时可以继续保持温和复述和熟悉线索引导。`;
}


function buildCareReminderSummary(reminders) {
    const enabled = reminders.filter((reminder) => reminder.is_enabled);
    if (!reminders.length) {
        return "当前还没有创建照护提醒。";
    }
    if (!enabled.length) {
        return `已创建 ${reminders.length} 条提醒，目前都处于关闭状态。`;
    }
    const labels = uniqueItems(enabled.map((reminder) => reminderTypeLabels[reminder.reminder_type] || reminder.title), 4);
    const confirmedCount = enabled.filter((reminder) => reminder.status === "confirmed").length;
    const pendingCount = enabled.filter((reminder) => ["pending", "reminded"].includes(reminder.status)).length;
    return `已启用 ${enabled.length} 条提醒，主要包括：${labels.join("、")}。已确认 ${confirmedCount} 条，待确认 ${pendingCount} 条。`;
}


function buildReminderStatusSummary(reminders) {
    const enabled = reminders.filter((reminder) => reminder.is_enabled);
    return {
        confirmed: enabled.filter((reminder) => reminder.status === "confirmed").length,
        pending: enabled.filter((reminder) => ["pending", "reminded"].includes(reminder.status)).length,
        missed: enabled.filter((reminder) => reminder.status === "missed").length,
        skipped: enabled.filter((reminder) => reminder.status === "skipped").length
    };
}


function buildCareEventSummary(events) {
    if (!events.length) {
        return "近期还没有异常事件记录。";
    }

    const counts = {};
    events.forEach((event) => {
        const label = eventTypeLabels[event.event_type] || "其他事件";
        counts[label] = (counts[label] || 0) + 1;
    });
    const summary = Object.entries(counts)
        .slice(0, 4)
        .map(([label, count]) => `${label} ${count} 次`)
        .join("、");
    const highCount = events.filter((event) => ["medium", "high"].includes(event.severity)).length;
    return highCount
        ? `近期记录 ${events.length} 条事件，其中 ${highCount} 条需要优先留意：${summary}。`
        : `近期记录 ${events.length} 条事件：${summary}。`;
}


function buildInteractionSummary(logs) {
    const turnCount = getConversationTurnCount(logs);
    if (!turnCount) {
        return "现在还在等待新的互动内容。";
    }

    const recentMessages = getRecentUserMessages(logs, 2);
    if (recentMessages.length) {
        return `最近的互动主要围绕 ${recentMessages.map((item) => `“${shortText(item, 14)}”`).join("、")} 展开。`;
    }

    return `最近已经完成 ${turnCount} 轮互动，整体仍保持在比较轻缓的节奏里。`;
}


function buildRiskSummary(profile, logs) {
    const repeatedCount = getRepeatedQuestionCount(logs);
    const digest = buildMemoryDigest(profile, logs);
    const shortInputs = getRecentUserMessages(logs, 4).filter((message) => message.length <= 3).length;

    if (!logs.length) {
        return "现在还没有足够的互动记录，先继续观察熟悉话题和接话节奏。";
    }

    if (repeatedCount >= 2 && digest.repeatedTopics.length) {
        return `最近更容易反复回到 ${digest.repeatedTopics.join("、")}，陪伴时可以优先从这些熟悉线索轻轻接住。`;
    }

    if (shortInputs >= 2) {
        return "最近更容易停在短句回应上，继续从家人、旧地方和熟悉经历慢慢带话题会更顺。";
    }

    if (digest.mentionedPeople.length || digest.lifeTopics.length || digest.preferenceTopics.length) {
        return "目前主要还是顺着熟悉的人和往事更容易接得上，暂时没有明显升高的风险点。";
    }

    return "当前互动节奏还算平稳，暂时没有特别突出的风险点。";
}


function countTodayChats(logs) {
    const today = formatDateKey(new Date());
    return logs.filter((log) => log.role === "user" && String(log.timestamp || "").slice(0, 10) === today).length;
}


function setTextIfPresent(id, text) {
    const node = element(id);
    if (node) {
        node.textContent = text;
    }
}


function renderSummaryPanels(profile, logs) {
    const memoryDigest = buildMemoryDigest(profile, logs);
    currentMemoryDigest = memoryDigest;
    const topicTags = extractTopicTags(logs, 3);
    const todayCount = countTodayChats(logs);
    const mentionedItems = extractMentionedItems(profile, logs, 4);

    updateSupportCopy();
    setTextIfPresent("remembered-preferences", buildRememberedPreferences(profile));
    setTextIfPresent("recent-topics", buildRecentTopicsSummary(profile, logs));
    setTextIfPresent("memory-summary-text", memoryDigest.summary);
    setTextIfPresent(
        "memory-life-topics",
        memoryDigest.lifeTopics.length
            ? `最近更容易接上的经历有：${memoryDigest.lifeTopics.join("、")}。`
            : "等聊过几句之后，这里会慢慢出现更熟悉的经历线索。",
    );
    setTextIfPresent(
        "memory-preference-topics",
        memoryDigest.preferenceTopics.length
            ? `更容易让 ta 愿意接着说的是：${memoryDigest.preferenceTopics.join("、")}。`
            : "这里会慢慢出现更容易让 ta 愿意继续说下去的偏好。",
    );
    setTextIfPresent(
        "memory-repeated-topics",
        memoryDigest.repeatedTopics.length
            ? `最近重复回到的话题有：${memoryDigest.repeatedTopics.join("、")}。`
            : "当前还没有明显重复回到的主题。",
    );
    setTextIfPresent("today-chat-count", `${todayCount} 次`);
    setTextIfPresent("recent-topic-tags", topicTags.length ? topicTags.join(" / ") : "还在等第一句话");
    setTextIfPresent(
        "notes-mentioned-items",
        memoryDigest.mentionedPeople.length
            ? `最近常被提到的人有：${memoryDigest.mentionedPeople.join("、")}。`
            : "最近还没有形成稳定的人物线索。",
    );
    setTextIfPresent("notes-follow-up-topics", buildFollowUpSummary(profile, logs));
    setTextIfPresent("notes-gentle-summary", buildNotesGentleSummary(profile, logs));
    setTextIfPresent("notes-stuck-points", buildStuckPointsSummary(profile, logs));
    setTextIfPresent("analysis-turn-count", String(getConversationTurnCount(logs)));
    setTextIfPresent("analysis-repeated-count", String(getRepeatedQuestionCount(logs)));
    setTextIfPresent("analysis-recent-activity", buildRecentActivityText(logs));
    setTextIfPresent("analysis-memory-summary", memoryDigest.summary);
    setTextIfPresent(
        "analysis-high-frequency-topics",
        memoryDigest.followUpTopics.length
            ? `眼下更容易顺着聊下去的是：${memoryDigest.followUpTopics.join("、")}。`
            : topicTags.length
                ? `最近比较常出现的是：${topicTags.join("、")}。`
                : "等聊过几句之后，这里会慢慢出现最近常被提到的话题。",
    );
    setTextIfPresent("analysis-repeat-summary", buildRepeatSummary(logs));
    setTextIfPresent("analysis-interaction-summary", buildWeeklyInteractionSummary(logs));
    setTextIfPresent("analysis-risk-summary", buildSensitiveTopicsSummary(profile, logs));
    setTextIfPresent("care-reminder-summary", buildCareReminderSummary(currentReminders));
    setTextIfPresent("care-event-summary", buildCareEventSummary(currentEventLogs));
    setTextIfPresent("analysis-reminder-count", String(currentReminders.filter((reminder) => reminder.is_enabled).length));
    setTextIfPresent("care-event-count", String(currentEventLogs.length));
    setTextIfPresent(
        "care-overview-people",
        memoryDigest.mentionedPeople.length ? memoryDigest.mentionedPeople.slice(0, 2).join("、") : "待积累",
    );
    setTextIfPresent(
        "care-overview-followup",
        memoryDigest.followUpTopics.length ? memoryDigest.followUpTopics.slice(0, 2).join("、") : "待积累",
    );
    setTextIfPresent(
        "care-overview-stuck",
        memoryDigest.repeatedTopics.length ? memoryDigest.repeatedTopics.join("、") : getRepeatedQuestionCount(logs) ? "需要继续观察" : "暂无明显卡点",
    );
    setTextIfPresent("analysis-weekly-activity", buildWeeklyInteractionSummary(logs));
    setTextIfPresent("analysis-follow-up-summary", buildFollowUpTopicText(profile, logs));
    setTextIfPresent("analysis-risk-points", buildSensitiveTopicsSummary(profile, logs));
}


function renderDashboardProfileCard(profile) {
    const container = element("dashboard-profile-card");
    if (!container) {
        return;
    }

    const patient = currentSelectedPatient && currentSelectedPatient.id ? currentSelectedPatient : null;
    const rows = patient ? [
        ["姓名", patient.name || "尚未填写"],
        ["年龄", patient.age ? `${patient.age} 岁` : "尚未填写"],
        ["与照护者关系", patient.relation || "尚未填写"],
        ["病情阶段", patient.stage || "尚未填写"],
        ["备注", patient.notes ? shortText(patient.notes, 38) : "尚未填写"]
    ] : [
        ["常用称呼", profile.name || "尚未填写"],
        ["熟悉城市", profile.hometown || "尚未填写"],
        ["重要的人", profile.family_info ? shortText(profile.family_info, 38) : "尚未填写"],
        ["熟悉经历", profile.life_events ? shortText(profile.life_events, 38) : "尚未填写"],
        ["喜欢的事情", profile.preferences ? shortText(profile.preferences, 38) : "尚未填写"]
    ];

    container.innerHTML = rows.map(([label, value]) => (
        `<div class="soft-list-row"><span>${label}</span><strong>${escapeHtml(value)}</strong></div>`
    )).join("");
}


function renderConversationPatientHeader(profile) {
    setTextIfPresent("conversation-patient-name", currentSelectedPatient.name || profile.name || "患者");
    setTextIfPresent("conversation-today-date", formatConversationDate());
}


function renderInitialMessages(logs = []) {
    const chatBox = element("chat-box");
    if (!chatBox) {
        return;
    }

    chatBox.innerHTML = "";

    if (!logs.length) {
        appendMessage("assistant", defaultWelcomeMessage, "", { immediate: true });
        return;
    }

    logs.forEach((log) => {
        appendMessage(log.role, log.message, buildMetaText(log), { scroll: false });
    });

    ensureConversationScrollAnchor(chatBox);
    updateConversationLayout();

    scrollConversationToLatest({ immediate: true });
}


function fillProfileForm(profile) {
    if (!profile || !hasProfileForm()) {
        return;
    }

    if (profile.id) {
        currentUserId = profile.id;
        element("profile-id").value = String(profile.id);
    }

    element("name").value = profile.name || "";
    element("age").value = profile.age ?? "";
    element("hometown").value = profile.hometown || "";
    element("family-info").value = profile.family_info || "";
    element("life-events").value = profile.life_events || "";
    element("preferences").value = profile.preferences || "";
    element("notes").value = profile.notes || "";
    updateSupportCopy();
}


async function loadProfile() {
    const params = new URLSearchParams();
    const legacyId = legacyProfileUserId();
    if (legacyId) {
        params.set("user_id", legacyId);
    }

    const query = params.toString();
    const url = query ? `/profile?${query}` : "/profile";

    try {
        const response = await fetch(url);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "资料加载失败");
        }

        currentProfile = { ...(data.profile || {}) };
        currentUserId = currentProfile.id || currentUserId;
        fillProfileForm(currentProfile);
        renderAll();
    } catch (error) {
        currentProfile = { ...(bootstrap.profile || {}) };
        fillProfileForm(currentProfile);
        renderAll();
        console.error(error);
    }
}


async function loadRecentChatLogs() {
    const params = new URLSearchParams();

    const legacyId = legacyProfileUserId();
    if (legacyId) {
        params.set("user_id", legacyId);
    }
    params.set("mode", getCurrentMode());
    params.set("limit", isPage("chat_history") ? "50" : "10");

    try {
        const response = await fetch(`/chat_logs?${params.toString()}`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "历史记录加载失败");
        }

        currentProfile = { ...(data.profile || currentProfile) };
        currentUserId = currentProfile.id || currentUserId;
        currentLogs = Array.isArray(data.logs) ? [...data.logs] : [];

        fillProfileForm(currentProfile);
        renderAll();
    } catch (error) {
        currentLogs = Array.isArray(bootstrap.recentLogs) ? [...bootstrap.recentLogs] : [];
        renderAll();
        console.error(error);
    }
}


async function loadCareData() {
    const legacyId = legacyProfileUserId();
    if (!currentUserId && !currentCaregiverPatientId) {
        return;
    }

    const params = new URLSearchParams({ user_profile_id: legacyId || "0" });

    try {
        const [reminderResponse, eventResponse, caregiverResponse, insightResponse, caregiverEventResponse, dailyCareResponse, dailyMoodResponse, riskEventResponse] = await Promise.all([
            fetch(`/reminders?${params.toString()}`),
            fetch(`/event_logs?${params.toString()}`),
            fetch(`/caregivers?${params.toString()}`),
            fetch(`/api/caregiver/${encodeURIComponent(currentCaregiverPatientId)}/summary`),
            fetch(`/api/caregiver/${encodeURIComponent(currentCaregiverPatientId)}/events`),
            fetch(`/api/daily-care/${encodeURIComponent(currentCaregiverPatientId)}/today`),
            fetch(`/api/daily-summary/${encodeURIComponent(currentCaregiverPatientId)}?days=1`),
            fetch(`/api/risk-events/${encodeURIComponent(currentCaregiverPatientId)}?days=1&unresolved_only=false`)
        ]);

        const reminderData = await reminderResponse.json();
        const eventData = await eventResponse.json();
        const caregiverData = await caregiverResponse.json();
        const insightData = await insightResponse.json();
        const caregiverEventData = await caregiverEventResponse.json();
        const dailyCareData = await dailyCareResponse.json();
        const dailyMoodData = await dailyMoodResponse.json();
        const riskEventData = await riskEventResponse.json();

        if (reminderResponse.ok) {
            currentReminders = Array.isArray(reminderData.reminders) ? [...reminderData.reminders] : [];
        }
        if (eventResponse.ok) {
            currentEventLogs = Array.isArray(eventData.event_logs) ? [...eventData.event_logs] : [];
        }
        if (caregiverResponse.ok) {
            currentCaregiverLinks = Array.isArray(caregiverData.caregiver_links) ? [...caregiverData.caregiver_links] : [];
        }
        if (insightResponse.ok) {
            currentCaregiverInsight = { ...insightData };
        }
        if (caregiverEventResponse.ok) {
            currentCaregiverEvents = Array.isArray(caregiverEventData.events) ? [...caregiverEventData.events] : [];
        }
        if (dailyCareResponse.ok) {
            currentDailyCareSummary = { ...dailyCareData };
        }
        if (dailyMoodResponse.ok && Array.isArray(dailyMoodData) && dailyMoodData.length) {
            currentDailyMoodSummary = { ...dailyMoodData[dailyMoodData.length - 1] };
        } else {
            currentDailyMoodSummary = {};
        }
        if (riskEventResponse.ok) {
            currentRiskEvents = Array.isArray(riskEventData) ? [...riskEventData] : [];
        }

        renderAll();
    } catch (error) {
        currentReminders = Array.isArray(bootstrap.reminders) ? [...bootstrap.reminders] : [];
        currentEventLogs = Array.isArray(bootstrap.eventLogs) ? [...bootstrap.eventLogs] : [];
        currentCaregiverLinks = Array.isArray(bootstrap.caregiverLinks) ? [...bootstrap.caregiverLinks] : [];
        currentCaregiverEvents = Array.isArray(bootstrap.caregiverEvents) ? [...bootstrap.caregiverEvents] : [];
        currentCaregiverInsight = bootstrap.caregiverInsight ? { ...bootstrap.caregiverInsight } : {};
        currentDailyCareSummary = bootstrap.dailyCareSummary ? { ...bootstrap.dailyCareSummary } : {};
        currentDailyMoodSummary = {};
        currentRiskEvents = [];
        renderAll();
        console.error(error);
    }
}


function buildMetaText(log) {
    void log;
    return "";
}


function appendMessage(role, message, metaText = "", options = {}) {
    const chatBox = element("chat-box");
    if (!chatBox) {
        return;
    }
    const anchor = ensureConversationScrollAnchor(chatBox);

    const wrapper = document.createElement("div");
    const label = document.createElement("div");
    const bubble = document.createElement("div");

    wrapper.className = `message ${role === "assistant" ? "assistant" : "user"}`;
    label.className = "message-label";
    bubble.className = "message-bubble";

    label.textContent = role === "assistant" ? "陪伴助手" : "你";
    bubble.textContent = message;

    wrapper.appendChild(label);
    wrapper.appendChild(bubble);

    if (metaText) {
        const meta = document.createElement("div");
        meta.className = "message-meta";
        meta.textContent = metaText;
        wrapper.appendChild(meta);
    }

    if (anchor && anchor.parentElement === chatBox) {
        chatBox.insertBefore(wrapper, anchor);
    } else {
        chatBox.appendChild(wrapper);
    }

    if (options.scroll !== false) {
        updateConversationLayout();
        scrollConversationToLatest({ immediate: Boolean(options.immediate) });
    }
}


function renderLogList(targetId, logs, options = {}) {
    const container = element(targetId);
    if (!container) {
        return;
    }

    if (!Array.isArray(logs) || !logs.length) {
        container.innerHTML = `
            <div class="log-empty">
                <strong>暂时还没有可回看的近期记录。</strong>
                <span>等有了新的互动，这里会自动整理最近片段，方便家属快速回看。</span>
            </div>
        `;
        return;
    }

    const recentLogs = options.compact ? logs.slice(-4) : logs.slice(-10);
    container.innerHTML = recentLogs.map((log) => `
        <article class="log-card ${log.role === "assistant" ? "assistant" : "user"}">
            <div class="log-card-header">
                <strong>${log.role === "assistant" ? "陪伴助手" : "你"}</strong>
                <span>${escapeHtml(formatDisplayTime(log.timestamp))}</span>
            </div>
            <p>${escapeHtml(log.message || "")}</p>
        </article>
    `).join("");
}


function renderReminderList(targetId, reminders) {
    const container = element(targetId);
    if (!container) {
        return;
    }

    if (!Array.isArray(reminders) || !reminders.length) {
        container.innerHTML = `
            <div class="log-empty">
                <strong>暂时还没有照护提醒。</strong>
                <span>可以先创建吃药、喝水、作息或活动提醒，后续再接入真实通知能力。</span>
            </div>
        `;
        return;
    }

    container.innerHTML = reminders.map((reminder) => `
        <article class="care-record-card">
            <div>
                <strong>${escapeHtml(reminder.title || reminderTypeLabels[reminder.reminder_type] || "照护提醒")}</strong>
                <span>${escapeHtml(reminderTypeLabels[reminder.reminder_type] || reminder.reminder_type)} · ${escapeHtml(reminder.scheduled_time || "未设置时间")} · ${escapeHtml(reminderStatusLabels[reminder.status] || reminder.status || "待确认")}</span>
                <span>${escapeHtml(reminder.description || "暂无说明")}</span>
                <span>设置人：${escapeHtml(reminder.created_by || "family")}</span>
            </div>
            <button type="button" class="toggle-chip reminder-toggle" data-reminder-id="${reminder.id}" data-enabled="${reminder.is_enabled ? "true" : "false"}">
                ${reminder.is_enabled ? "开启" : "关闭"}
            </button>
            <button type="button" class="toggle-chip reminder-edit" data-reminder-id="${reminder.id}">编辑</button>
        </article>
    `).join("");

    container.querySelectorAll(".reminder-toggle").forEach((button) => {
        button.addEventListener("click", () => {
            const reminderId = Number(button.dataset.reminderId);
            const nextEnabled = button.dataset.enabled !== "true";
            toggleReminder(reminderId, nextEnabled);
        });
    });
    container.querySelectorAll(".reminder-edit").forEach((button) => {
        button.addEventListener("click", () => {
            const reminderId = Number(button.dataset.reminderId);
            editReminder(reminderId);
        });
    });
}


function renderEventLogList(targetId, events, options = {}) {
    const container = element(targetId);
    if (!container) {
        return;
    }

    if (!Array.isArray(events) || !events.length) {
        container.innerHTML = `
            <div class="log-empty">
                <strong>近期还没有异常事件记录。</strong>
                <span>如出现拒药、夜间异常、离家倾向等情况，可以在对应页面记录。</span>
            </div>
        `;
        return;
    }

    const visibleEvents = options.compact ? events.slice(0, 4) : events.slice(0, 8);
    container.innerHTML = visibleEvents.map((event) => `
        <article class="care-record-card">
            <div>
                <strong>${escapeHtml(eventTypeLabels[event.event_type] || "其他事件")}</strong>
                <span>严重度：${escapeHtml(severityLabels[event.severity] || event.severity)} · 来源：${escapeHtml(event.source || "caregiver")}</span>
                <p>${escapeHtml(event.description || "未填写说明。")}</p>
            </div>
            <time>${escapeHtml(String(event.created_at || "").slice(5, 16).replace("T", " "))}</time>
        </article>
    `).join("");
}


function renderCaregiverInsight() {
    const summaryNode = element("caregiver-today-summary");
    if (!summaryNode) {
        return;
    }

    const insight = currentCaregiverInsight || {};
    const topEvents = Array.isArray(insight.top_events) && insight.top_events.length
        ? insight.top_events
        : currentCaregiverEvents;
    const actions = Array.isArray(insight.suggested_actions) ? insight.suggested_actions : [];

    const patientName = currentSelectedPatient.name || currentProfile.name || "患者";
    summaryNode.textContent = insight.today_summary || `${patientName}今天暂无新的照护摘要，完成对话或记录事件后会在这里更新。`;

    const riskNode = element("caregiver-insight-risk-level");
    if (riskNode) {
        const risk = insight.risk_level || "medium";
        riskNode.textContent = `${severityLabels[risk] || risk} · Care insight`;
        riskNode.className = "status-pill";
        if (risk === "high" || risk === "medium") {
            riskNode.classList.add("warning");
        } else {
            riskNode.classList.add("success");
        }
    }

    const riskList = element("caregiver-risk-list");
    if (riskList) {
        const visibleEvents = topEvents.filter((event) => !event.resolved).slice(0, 5);
        riskList.innerHTML = visibleEvents.length
            ? visibleEvents.map((event) => `
                <div class="caregiver-insight-row">
                    <strong>${escapeHtml(severityLabels[event.severity] || event.severity || "中")}</strong>
                    <span>${escapeHtml(event.title || eventTypeLabels[event.event_type] || event.event_type || "照护事件")}：${escapeHtml(event.description || event.source_message || "需要家属留意")}</span>
                </div>
            `).join("")
            : `<div class="caregiver-insight-row">当前暂无未处理风险提醒。</div>`;
    }

    const actionList = element("caregiver-action-list");
    if (actionList) {
        const fallbackActions = [
            "晚上给患者打一通电话。",
            "确认今日药物是否已服用。",
            "补充一段女儿语音留言。"
        ];
        const visibleActions = actions.length ? actions : fallbackActions;
        actionList.innerHTML = visibleActions.slice(0, 5).map((action) => `
            <div class="caregiver-insight-row">${escapeHtml(action)}</div>
        `).join("");
    }
}

function renderAnalysisCurrentDate() {
    const node = element("analysis-current-date");
    if (!node) {
        return;
    }
    node.textContent = formatConversationDate(new Date());
}


function renderReminderStatusCard(reminders = currentReminders) {
    const container = element("analysis-reminder-status-list");
    if (!container) {
        return;
    }
    const summary = buildReminderStatusSummary(Array.isArray(reminders) ? reminders : []);
    container.innerHTML = [
        ["已确认", summary.confirmed],
        ["待确认", summary.pending],
        ["未完成", summary.missed],
        ["跳过", summary.skipped]
    ].map(([label, count]) => `
        <div class="caregiver-insight-row">
            <strong>${escapeHtml(label)}</strong>
            <span>${count}</span>
        </div>
    `).join("");
}


function dailyCareStatusLabel(status) {
    return {
        stable: "平稳",
        needs_attention: "需要关注",
        high_risk: "高风险"
    }[String(status || "").toLowerCase()] || (status || "待更新");
}


function applyStatusPillClass(node, status) {
    if (!node) {
        return;
    }
    node.className = "status-pill";
    const normalized = String(status || "").toLowerCase();
    if (["stable", "confirmed", "low", "resolved"].includes(normalized)) {
        node.classList.add("success");
    } else if (["high_risk", "missed", "high", "unresolved"].includes(normalized)) {
        node.classList.add("danger");
    } else if (["needs_attention", "pending", "medium"].includes(normalized)) {
        node.classList.add("warning");
    } else {
        node.classList.add("neutral");
    }
}


function renderDailyCareLoop() {
    const summary = currentDailyCareSummary || {};
    const statusNode = element("daily-care-overall-status");
    if (statusNode) {
        const status = summary.overall_status || "needs_attention";
        statusNode.textContent = dailyCareStatusLabel(status);
        applyStatusPillClass(statusNode, status);
    }

    const reminderSummary = summary.reminder_summary || {};
    setTextIfPresent("daily-care-total", String(reminderSummary.total ?? reminderSummary.enabled_total ?? currentReminders.filter((reminder) => reminder.is_enabled).length));
    setTextIfPresent("daily-care-confirmed", String(reminderSummary.confirmed ?? 0));
    setTextIfPresent("daily-care-pending", String(reminderSummary.pending ?? 0));
    setTextIfPresent("daily-care-missed", String(reminderSummary.missed ?? 0));
    setTextIfPresent("daily-care-skipped", String(reminderSummary.skipped ?? 0));

    const riskSummary = summary.risk_summary || {};
    setTextIfPresent("daily-care-risk-high", String(riskSummary.high ?? 0));
    setTextIfPresent("daily-care-risk-medium", String(riskSummary.medium ?? 0));
    setTextIfPresent("daily-care-risk-low", String(riskSummary.low ?? 0));
    const unresolvedCount = Number(riskSummary.unresolved || 0);
    setTextIfPresent("daily-care-unresolved", String(unresolvedCount));

    const actionsNode = element("daily-care-suggested-actions");
    if (actionsNode) {
        const actions = Array.isArray(summary.suggested_actions) ? summary.suggested_actions : [];
        actionsNode.innerHTML = actions.length
            ? actions.slice(0, 3).map((action) => `<div class="analysis-mini-item">${escapeHtml(action)}</div>`).join("")
            : `<div class="analysis-mini-item">暂无异常，建议继续保持日常提醒和晚间联系。</div>`;
    }
}


function renderDashboardMoodCard() {
    const mood = currentDailyMoodSummary || {};
    const labelNode = element("dashboard-mood-label");
    const scoreNode = element("dashboard-mood-score");
    const evidenceNode = element("dashboard-mood-evidence");
    const moodScore = mood.mood_score === null || mood.mood_score === undefined ? null : Number(mood.mood_score);
    const today = new Date();
    const todayText = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;

    if (!mood || mood.date !== todayText || moodScore === null || Number.isNaN(moodScore)) {
        setTextIfPresent("dashboard-mood-label", "暂无数据");
        setTextIfPresent("dashboard-mood-score", "今日还没有对话");
        setTextIfPresent("dashboard-mood-evidence", "完成一次患者对话后，系统会在后台更新情绪趋势。");
        return;
    }

    if (labelNode) {
        labelNode.textContent = mood.mood_label || "未知";
    }
    if (scoreNode) {
        scoreNode.textContent = `${moodScore.toFixed(1)}/5`;
    }
    if (evidenceNode) {
        evidenceNode.textContent = mood.mood_evidence || mood.evidence || mood.summary_text || "暂无情绪判断依据。";
    }
}


function renderDashboardCarePolish() {
    const todayDate = element("dashboard-today-date");
    if (todayDate) {
        todayDate.textContent = formatConversationDate();
    }
    renderDashboardMedicationStatus();
    renderDashboardRiskEvents();
}


function renderDashboardMedicationStatus() {
    const node = element("dashboard-medication-status");
    if (!node) {
        return;
    }
    const today = new Date();
    const todayText = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;
    const dailySummaryIsToday = currentDailyMoodSummary?.date === todayText;
    const medicationTaken = dailySummaryIsToday
        ? currentDailyMoodSummary?.medication_taken
        : currentDailyCareSummary?.medication_taken;
    const medicationTime = dailySummaryIsToday
        ? currentDailyMoodSummary?.medication_time
        : currentDailyCareSummary?.medication_time;
    let statusClass = "status-pending";
    let title = "⏳ 待确认";
    let detail = "还没有记录今日服药情况。";
    let action = `<button id="dashboard-mark-medication-taken-button" type="button" class="ghost-button dashboard-medication-action">标记已服药</button>`;
    if (medicationTaken === 1 || medicationTaken === true) {
        statusClass = "status-taken";
        title = "✅ 已服药";
        detail = medicationTime ? `实际服药时间 ${medicationTime}` : "今日已确认服药。";
        action = `<button type="button" class="ghost-button dashboard-medication-action" disabled>已记录</button>`;
    }
    node.className = `dashboard-medication-status ${statusClass}`;
    node.innerHTML = `<strong>${title}</strong><span>${escapeHtml(detail)}</span>${action}`;
    element("dashboard-mark-medication-taken-button")?.addEventListener("click", markDashboardMedicationTaken);
}


function renderDashboardRiskEvents() {
    const container = element("dashboard-risk-event-list");
    if (!container) {
        return;
    }
    const events = (Array.isArray(currentRiskEvents) ? currentRiskEvents : []).slice(0, 8);
    renderHighRiskBanner(events);
    if (!events.length) {
        container.innerHTML = `<div class="log-empty dashboard-risk-empty"><strong>今日无风险事件 ✅</strong><span>如果患者出现外出、焦虑或用药不确定，会在这里聚合展示。</span></div>`;
        return;
    }
    container.innerHTML = events.map((event) => {
        const riskLevel = String(event.risk_level || "低");
        const severity = riskLevel === "高" ? "high" : riskLevel === "中" ? "medium" : "low";
        const resolved = Number(event.is_resolved || 0) === 1;
        const timeText = formatDisplayTime(event.created_at || "");
        return `
            <article class="dashboard-risk-event ${severity === "high" ? "high-risk" : ""} ${resolved ? "resolved" : ""}">
                <div>
                    <time>${escapeHtml(timeText || "今日")}</time>
                    <strong>${escapeHtml(event.risk_type || "照护风险")}</strong>
                    <p><b>触发原文：</b>${escapeHtml(shortText(event.evidence || "未记录", 30))}</p>
                    <p><b>建议：</b>${escapeHtml(event.suggestion || "建议照护者稍后确认患者状态。")}</p>
                    ${resolved ? `<span class="dashboard-risk-resolved">已处理</span>` : `<button type="button" class="ghost-button dashboard-risk-resolve" data-event-id="${escapeHtml(event.id)}">✅ 标记已处理</button>`}
                </div>
                <span class="severity-badge severity-${escapeHtml(severity)}">${escapeHtml(riskLevel)}</span>
            </article>
        `;
    }).join("");
    container.querySelectorAll(".dashboard-risk-resolve").forEach((button) => {
        button.addEventListener("click", () => resolveRiskEvent(button.dataset.eventId || "", button));
    });
}


function renderHighRiskBanner(events = currentRiskEvents) {
    const existing = element("dashboard-high-risk-banner");
    if (existing) {
        existing.remove();
    }
    const highRisk = (Array.isArray(events) ? events : []).find((event) => event.risk_level === "高" && Number(event.is_resolved || 0) !== 1);
    if (!highRisk || !isPage("dashboard")) {
        return;
    }
    const banner = document.createElement("div");
    banner.id = "dashboard-high-risk-banner";
    banner.className = "dashboard-high-risk-banner";
    banner.innerHTML = `
        <strong>⚠️ 检测到高风险信号：${escapeHtml(highRisk.risk_type || "照护风险")} — ${escapeHtml(highRisk.suggestion || "请尽快确认患者状态。")}</strong>
        <button type="button" aria-label="关闭高风险提醒">关闭</button>
    `;
    banner.querySelector("button")?.addEventListener("click", () => banner.remove());
    document.body.appendChild(banner);
}


async function resolveRiskEvent(eventId, sourceButton = null) {
    if (!eventId) {
        return;
    }
    try {
        if (sourceButton) {
            sourceButton.disabled = true;
            sourceButton.textContent = "处理中";
        }
        const response = await fetch(`/api/risk-events/${encodeURIComponent(eventId)}/resolve`, { method: "POST" });
        const data = await response.json();
        if (!response.ok || !data.ok) {
            throw new Error(data.detail || "风险事件处理失败");
        }
        await loadCareData();
    } catch (error) {
        if (sourceButton) {
            sourceButton.disabled = false;
            sourceButton.textContent = "✅ 标记已处理";
        }
        console.error(error);
    }
}


async function recordTodayFromDashboard() {
    const button = element("dashboard-record-today-button");
    if (!currentCaregiverPatientId || !button) {
        return;
    }
    const originalText = button.textContent;
    try {
        button.disabled = true;
        button.textContent = "记录中";
        const response = await fetch(`/api/daily-summary/${encodeURIComponent(currentCaregiverPatientId)}`, {
            method: "POST"
        });
        if (!response.ok) {
            throw new Error("record failed");
        }
        setTextIfPresent("dashboard-record-today-status", "✅ 今日记录已保存");
        await loadCareData();
    } catch (error) {
        setTextIfPresent("dashboard-record-today-status", "记录今日暂时失败，请稍后再试。");
    } finally {
        button.disabled = false;
        button.textContent = originalText || "记录今日";
    }
}


async function markDashboardMedicationTaken() {
    const button = element("dashboard-mark-medication-taken-button");
    if (!currentCaregiverPatientId || !button) {
        return;
    }
    try {
        button.disabled = true;
        button.textContent = "记录中";
        const response = await fetch(`/api/medication-taken/${encodeURIComponent(currentCaregiverPatientId)}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ schedule_id: 0 })
        });
        const data = await response.json();
        if (!response.ok || data.ok !== true) {
            throw new Error("medication taken failed");
        }
        const now = new Date();
        const timeText = `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;
        const dateText = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
        currentDailyMoodSummary = {
            ...currentDailyMoodSummary,
            date: dateText,
            medication_taken: 1,
            medication_time: timeText
        };
        currentDailyCareSummary = {
            ...currentDailyCareSummary,
            medication_taken: 1,
            medication_time: timeText
        };
        renderDashboardMedicationStatus();
        await loadCareData();
    } catch (error) {
        button.disabled = false;
        button.textContent = "标记已服药";
    }
}


function normalizeMedicationSchedulePayload(data) {
    if (Array.isArray(data)) {
        return {
            reminders: data,
            schedules: data
        };
    }
    return {
        reminders: Array.isArray(data?.reminders) ? data.reminders : [],
        schedules: Array.isArray(data?.schedules) ? data.schedules : (Array.isArray(data?.reminders) ? data.reminders : [])
    };
}


async function loadMedicationSchedules(options = {}) {
    if (!currentCaregiverPatientId) {
        return [];
    }
    try {
        const response = await fetch(`/api/reminders/${encodeURIComponent(currentCaregiverPatientId)}`);
        if (!response.ok) {
            return null;
        }
        const data = normalizeMedicationSchedulePayload(await response.json());
        currentMedicationSchedules = [...data.schedules];
        if (options.render) {
            renderMedicationScheduleSettings();
        }
        return data.reminders;
    } catch (error) {
        if (!options.silent) {
            setTextIfPresent("medication-schedule-status", "用药提醒暂时加载失败，请稍后再试。");
        }
        return null;
    }
}


function bindMedicationScheduleSettings() {
    const addButton = element("add-medication-schedule-button");
    if (addButton) {
        addButton.addEventListener("click", addMedicationSchedule);
    }
}


function renderMedicationScheduleSettings() {
    const container = element("medication-schedule-list");
    if (!container) {
        return;
    }
    if (!currentMedicationSchedules.length) {
        container.innerHTML = `<div class="care-record-card"><div><strong>还没有用药提醒</strong><span>添加药品名称、时间和剂量后，到点会在工作台顶部弹出提醒。</span></div></div>`;
        return;
    }

    container.innerHTML = currentMedicationSchedules.map((schedule) => {
        const enabled = Boolean(schedule.enabled);
        const doseText = schedule.dose ? ` · ${escapeHtml(schedule.dose)}` : "";
        const notifiedText = schedule.notified ? "今日已记录服药" : "今日待提醒";
        return `
            <div class="care-record-card">
                <div>
                    <strong>${escapeHtml(schedule.remind_time || "--:--")} · ${escapeHtml(schedule.medication_name || "用药提醒")}</strong>
                    <span>${enabled ? "已启用" : "已暂停"}${doseText}</span>
                    <p>${notifiedText}</p>
                </div>
                <div class="medication-schedule-card-actions">
                    <button
                        type="button"
                        class="medication-schedule-toggle"
                        data-schedule-id="${schedule.id}"
                        data-enabled="${enabled ? "true" : "false"}"
                    >${enabled ? "暂停" : "启用"}</button>
                </div>
            </div>
        `;
    }).join("");

    container.querySelectorAll(".medication-schedule-toggle").forEach((button) => {
        button.addEventListener("click", () => {
            const scheduleId = Number(button.dataset.scheduleId);
            const nextEnabled = button.dataset.enabled !== "true";
            toggleMedicationSchedule(scheduleId, nextEnabled);
        });
    });
}


async function addMedicationSchedule() {
    const nameInput = element("medication-name-input");
    const timeInput = element("medication-time-input");
    const doseInput = element("medication-dose-input");
    const addButton = element("add-medication-schedule-button");
    const payload = {
        medication_name: nameInput?.value.trim() || "",
        remind_time: timeInput?.value || "",
        dose: doseInput?.value.trim() || ""
    };
    if (!payload.medication_name || !payload.remind_time) {
        setTextIfPresent("medication-schedule-status", "请填写药品名称和提醒时间。");
        return;
    }

    try {
        if (addButton) {
            addButton.disabled = true;
            addButton.textContent = "添加中";
        }
        const response = await fetch(`/api/reminders/${encodeURIComponent(currentCaregiverPatientId)}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error("schedule save failed");
        }
        [nameInput, timeInput, doseInput].forEach((node) => {
            if (node) {
                node.value = "";
            }
        });
        setTextIfPresent("medication-schedule-status", data.id ? "用药提醒已添加。" : "用药提醒已保存。");
        await loadMedicationSchedules({ render: true, silent: false });
    } catch (error) {
        setTextIfPresent("medication-schedule-status", "用药提醒暂时没有保存成功，请稍后再试。");
    } finally {
        if (addButton) {
            addButton.disabled = false;
            addButton.textContent = "添加提醒";
        }
    }
}


async function toggleMedicationSchedule(scheduleId, enabled) {
    if (!scheduleId) {
        return;
    }
    try {
        const response = await fetch(`/api/reminders/${encodeURIComponent(scheduleId)}/toggle`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ enabled })
        });
        if (!response.ok) {
            throw new Error("schedule toggle failed");
        }
        currentMedicationSchedules = currentMedicationSchedules.map((schedule) => (
            Number(schedule.id) === Number(scheduleId)
                ? { ...schedule, enabled }
                : schedule
        ));
        setTextIfPresent("medication-schedule-status", enabled ? "提醒已启用。" : "提醒已暂停。");
        renderMedicationScheduleSettings();
        await loadMedicationSchedules({ render: true });
    } catch (error) {
        setTextIfPresent("medication-schedule-status", "提醒状态暂时没有更新成功。");
    }
}


function startMedicationReminderPolling() {
    if (medicationReminderPollTimer) {
        window.clearInterval(medicationReminderPollTimer);
    }
    pollMedicationReminders();
    medicationReminderPollTimer = window.setInterval(pollMedicationReminders, 60 * 1000);
}


async function pollMedicationReminders() {
    const reminders = await loadMedicationSchedules({ render: true, silent: true });
    if (reminders === null) {
        return;
    }
    if (!Array.isArray(reminders) || !reminders.length) {
        hideMedicationReminderBanner();
        return;
    }
    if (reminders.every((item) => item.notified)) {
        hideMedicationReminderBanner();
        return;
    }
    const dueReminder = reminders.find((item) => isMedicationReminderDue(item));
    if (dueReminder) {
        showMedicationReminderBanner(dueReminder);
    }
}


function minutesFromTimeText(timeText) {
    const [hourText, minuteText] = String(timeText || "").split(":");
    const hours = Number(hourText);
    const minutes = Number(minuteText);
    if (Number.isNaN(hours) || Number.isNaN(minutes)) {
        return null;
    }
    return hours * 60 + minutes;
}


function isMedicationReminderDue(reminder) {
    if (!reminder || reminder.notified || reminder.enabled === false) {
        return false;
    }
    const scheduleId = Number(reminder.id);
    const snoozeUntil = medicationSnoozeUntilById.get(scheduleId);
    if (snoozeUntil) {
        return Date.now() >= snoozeUntil;
    }
    if (shownMedicationReminderIds.has(scheduleId)) {
        return false;
    }

    const reminderMinutes = minutesFromTimeText(reminder.remind_time);
    if (reminderMinutes === null) {
        return false;
    }
    const now = new Date();
    const nowMinutes = now.getHours() * 60 + now.getMinutes();
    const diff = Math.abs(nowMinutes - reminderMinutes);
    return Math.min(diff, 24 * 60 - diff) <= 5;
}


function showMedicationReminderBanner(reminder) {
    const banner = element("medication-reminder-banner");
    if (!banner) {
        return;
    }
    if (activeMedicationReminder && Number(activeMedicationReminder.id) === Number(reminder.id) && !banner.hidden) {
        return;
    }
    activeMedicationReminder = { ...reminder };
    shownMedicationReminderIds.add(Number(reminder.id));
    const doseText = reminder.dose ? `（${escapeHtml(reminder.dose)}）` : "";
    banner.innerHTML = `
        <strong>💊 ${escapeHtml(reminder.medication_name || "用药")} 用药时间到了${doseText}</strong>
        <div class="medication-reminder-banner-actions">
            <button type="button" id="medication-taken-button">✅ 已服药</button>
            <button type="button" id="medication-snooze-button">⏰ 稍后提醒（30分钟）</button>
        </div>
    `;
    banner.hidden = false;
    element("medication-taken-button")?.addEventListener("click", markMedicationTaken);
    element("medication-snooze-button")?.addEventListener("click", snoozeMedicationReminder);
}


function hideMedicationReminderBanner() {
    const banner = element("medication-reminder-banner");
    if (banner) {
        banner.hidden = true;
        banner.innerHTML = "";
    }
    activeMedicationReminder = null;
}


async function markMedicationTaken() {
    if (!currentCaregiverPatientId) {
        return;
    }
    try {
        const response = await fetch(`/api/medication-taken/${encodeURIComponent(currentCaregiverPatientId)}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                schedule_id: activeMedicationReminder?.id || 0
            })
        });
        if (!response.ok) {
            return;
        }
        currentMedicationSchedules = currentMedicationSchedules.map((schedule) => ({
            ...schedule,
            notified: true
        }));
        medicationSnoozeUntilById.clear();
        shownMedicationReminderIds.clear();
        hideMedicationReminderBanner();
        renderMedicationScheduleSettings();
        await loadCareData();
    } catch (error) {
        return;
    }
}


function snoozeMedicationReminder() {
    if (activeMedicationReminder?.id) {
        const scheduleId = Number(activeMedicationReminder.id);
        medicationSnoozeUntilById.set(scheduleId, Date.now() + 30 * 60 * 1000);
        shownMedicationReminderIds.delete(scheduleId);
    }
    hideMedicationReminderBanner();
}


function reminderTypeLabel(type, title = "") {
    const normalizedTitle = String(title || "");
    if (normalizedTitle.includes("午饭")) {
        return "午饭";
    }
    if (normalizedTitle.includes("晚饭")) {
        return "晚饭";
    }
    if (normalizedTitle.includes("小雨") || normalizedTitle.includes("电话")) {
        return "小雨电话";
    }
    if (normalizedTitle.includes("睡")) {
        return "睡前";
    }
    return reminderTypeLabels[type] || type || "照护提醒";
}


function reminderStatusClass(status) {
    const normalized = String(status || "pending").toLowerCase();
    if (normalized === "confirmed") {
        return "success";
    }
    if (normalized === "missed") {
        return "danger";
    }
    if (normalized === "skipped") {
        return "neutral";
    }
    return "warning";
}


function renderAnalysisReminderTasks(reminders = currentReminders) {
    const container = element("analysis-reminder-task-list");
    if (!container) {
        return;
    }
    if (!Array.isArray(reminders) || !reminders.length) {
        container.innerHTML = `
            <div class="log-empty">
                <strong>今天还没有提醒任务。</strong>
                <span>先到提醒中心创建吃药、用餐或电话提醒。</span>
            </div>
        `;
        return;
    }
    const enabled = reminders.filter((item) => item.is_enabled);
    if (!enabled.length) {
        container.innerHTML = `
            <div class="log-empty">
                <strong>今天还没有开启中的提醒任务。</strong>
                <span>可到提醒中心开启吃药、用餐、电话或睡前提醒。</span>
            </div>
        `;
        return;
    }
    container.innerHTML = enabled.map((reminder) => {
        const status = reminder.status || "pending";
        const typeLabel = reminderTypeLabel(reminder.reminder_type, reminder.title);
        const isMedication = reminder.reminder_type === "medication" || String(reminder.title || "").includes("药");
        const confirmedMeta = reminder.confirmed_at
            ? `确认人：${reminder.confirmed_by || "unknown"} · ${String(reminder.confirmed_at).replace("T", " ").slice(0, 16)}`
            : reminder.confirmed_by && reminder.confirmed_by !== "unknown"
                ? `确认人：${reminder.confirmed_by}`
                : "";
        return `
        <article class="analysis-task-card">
            <div class="analysis-task-main">
                <div class="analysis-task-time">${escapeHtml(reminder.scheduled_time || "--:--")}</div>
                <div>
                    <div class="analysis-task-title-row">
                        <strong>${escapeHtml(reminder.title || reminderTypeLabels[reminder.reminder_type] || "照护提醒")}</strong>
                        <span class="status-pill ${reminderStatusClass(status)}">${escapeHtml(reminderStatusLabels[status] || status || "待确认")}</span>
                    </div>
                    <span class="analysis-task-type">${escapeHtml(typeLabel)}</span>
                    <p>${escapeHtml(reminder.description || "暂无说明。")}</p>
                    ${confirmedMeta ? `<small>${escapeHtml(confirmedMeta)}</small>` : ""}
                    ${isMedication ? `<small class="analysis-medication-note">用药状态用于患者端回答，系统不会让 LLM 猜测用药事实。</small>` : ""}
                </div>
            </div>
            <div class="analysis-task-actions">
                <button type="button" class="ghost-button reminder-status-action" data-reminder-id="${reminder.id}" data-action="confirm">已确认</button>
                <button type="button" class="ghost-button reminder-status-action" data-reminder-id="${reminder.id}" data-action="miss">未完成</button>
                <button type="button" class="ghost-button reminder-status-action" data-reminder-id="${reminder.id}" data-action="skip">跳过</button>
            </div>
        </article>
    `;
    }).join("");
    container.querySelectorAll(".reminder-status-action").forEach((button) => {
        button.addEventListener("click", () => {
            const reminderId = Number(button.dataset.reminderId);
            const action = button.dataset.action || "confirm";
            updateReminderTaskStatus(reminderId, action, button);
        });
    });
}


function severityClass(severity) {
    return `severity-${String(severity || "low").toLowerCase()}`;
}


function renderCaregiverEventDetails(targetId = "caregiver-event-detail-list", events = currentCaregiverEvents) {
    const container = element(targetId);
    if (!container) {
        return;
    }
    const list = Array.isArray(events) ? events : [];
    const unresolved = list.filter((event) => !event.resolved);
    setTextIfPresent("caregiver-unresolved-count", `未处理 ${unresolved.length}`);

    if (!list.length) {
        container.innerHTML = `
            <div class="log-empty">
                <strong>暂无风险事件。</strong>
                <span>可以到患者端测试：“我是不是还没吃药？”、“我要回家”、“我想出去走走”。</span>
            </div>
        `;
        return;
    }
    const groups = [
        ["high", "高风险", list.filter((event) => !event.resolved && event.severity === "high")],
        ["medium", "中风险", list.filter((event) => !event.resolved && event.severity === "medium")],
        ["low", "低风险", list.filter((event) => !event.resolved && (!event.severity || event.severity === "low"))],
        ["resolved", "已处理", list.filter((event) => event.resolved)]
    ];

    container.innerHTML = groups.map(([key, label, group]) => `
        <section class="analysis-event-group">
            <h3>${escapeHtml(label)} <span>${group.length}</span></h3>
            <div class="analysis-card-list">
                ${group.length ? group.slice(0, 6).map((event) => `
                    <article class="analysis-event-card">
                        <div class="caregiver-event-card-head">
                            <span class="severity-badge ${key === "resolved" ? "severity-low" : severityClass(event.severity)}">${escapeHtml(key === "resolved" ? "已处理" : (severityLabels[event.severity] || event.severity || "低"))}</span>
                            <strong>${escapeHtml(eventTypeLabels[event.event_type] || event.title || event.event_type || "照护事件")}</strong>
                            <span class="resolve-pill">${event.resolved ? "已处理" : "未处理"}</span>
                        </div>
                        <p class="event-source">${escapeHtml(event.source_message || event.description || "暂无原始消息。")}</p>
                        <p class="event-action">${escapeHtml(event.suggested_action || "建议家属稍后确认患者状态。")}</p>
                        <time>${escapeHtml(String(event.created_at || "").replace("T", " ").slice(0, 16))}</time>
                        ${event.resolved ? "" : `<button type="button" class="ghost-button caregiver-event-resolve-action" data-event-id="${escapeHtml(event.id || "")}">标记已处理</button>`}
                    </article>
                `).join("") : `<div class="analysis-empty-inline">暂无${escapeHtml(label)}事件。</div>`}
            </div>
        </section>
    `).join("");

    container.querySelectorAll(".caregiver-event-resolve-action").forEach((button) => {
        button.addEventListener("click", () => {
            resolveCaregiverEvent(button.dataset.eventId || "", button);
        });
    });
}


async function loadFamiliarMaterials() {
    if (!currentUserId) {
        return;
    }
    try {
        const response = await fetch(`/api/materials/${encodeURIComponent(currentUserId)}`);
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "熟悉素材加载失败");
        }
        currentFamiliarMaterials = Array.isArray(data.materials) ? [...data.materials] : [];
        currentFamiliarMaterialStatus = data.status ? { ...data.status } : {};
        renderAll();
    } catch (error) {
        currentFamiliarMaterials = Array.isArray(bootstrap.familiarMaterials) ? [...bootstrap.familiarMaterials] : [];
        currentFamiliarMaterialStatus = bootstrap.familiarMaterialStatus ? { ...bootstrap.familiarMaterialStatus } : {};
        renderAll();
        console.error(error);
    }
}


async function loadMemoryCandidates() {
    if (!currentUserId) {
        return;
    }
    try {
        const response = await fetch(`/api/memory-candidates/${encodeURIComponent(currentUserId)}`);
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "记忆候选加载失败");
        }
        currentMemoryCandidates = Array.isArray(data.candidates) ? [...data.candidates] : [];
        renderAll();
    } catch (error) {
        currentMemoryCandidates = Array.isArray(bootstrap.memoryCandidates) ? [...bootstrap.memoryCandidates] : [];
        renderAll();
        console.error(error);
    }
}


function materialStatusText(enabled) {
    return enabled ? "已配置" : "未配置";
}


function renderMaterialStatusSummary() {
    const grid = element("analysis-material-status-grid") || element("materials-status-grid");
    if (!grid) {
        return;
    }
    const counts = currentFamiliarMaterials.reduce((acc, material) => {
        const key = material.material_type || "old_event";
        acc[key] = (acc[key] || 0) + 1;
        return acc;
    }, {});
    const rows = [
        ["家人照片", counts.family_photo || 0],
        ["语音留言", counts.voice_message || 0],
        ["熟悉音乐", counts.familiar_music || 0],
        ["旧地点", counts.old_place || 0],
        ["旧事件", counts.old_event || 0],
        ["敏感记忆", counts.sensitive_memory || 0]
    ];
    grid.innerHTML = rows.map(([label, value]) => `
        <div class="analysis-status-item ${Number(value) > 0 ? "ready" : "missing"}">
            <span>${escapeHtml(label)}</span>
            <strong>${escapeHtml(String(value))}</strong>
        </div>
    `).join("");
}


function setReminiscenceStatus(message, kind = "neutral") {
    const node = element("reminiscence-page-status");
    if (!node) {
        return;
    }
    if (!message) {
        node.textContent = "";
        node.className = "materials-form-status materials-form-status-hidden";
        return;
    }
    node.textContent = message;
    node.className = `materials-form-status materials-form-status-${kind}`;
}


function normalizeReminiscenceCategory(category) {
    return reminiscenceCategories.includes(category) ? category : "其他";
}


function normalizeReminiscenceMemory(memory, category = "其他") {
    const metadata = memory?.metadata && typeof memory.metadata === "object" ? memory.metadata : {};
    return {
        memory_id: String(memory?.memory_id || memory?.id || ""),
        text: String(memory?.text || memory?.document || ""),
        category: normalizeReminiscenceCategory(memory?.category || metadata.category || category),
        score: typeof memory?.score === "number" ? memory.score : null,
        approved_at: String(memory?.approved_at || metadata.approved_at || metadata.updated_at || metadata.created_at || ""),
        source: String(memory?.source || metadata.source || metadata.source_message || metadata.conversation_id || ""),
        metadata,
    };
}


function normalizeReminiscenceGroups(data) {
    const groups = {};
    reminiscenceCategories.forEach((category) => {
        const items = Array.isArray(data?.[category]) ? data[category] : [];
        groups[category] = items.map((item) => normalizeReminiscenceMemory(item, category)).filter((item) => item.memory_id && item.text);
    });
    return groups;
}


function allReminiscenceMemories() {
    return reminiscenceCategories.flatMap((category) => currentReminiscenceMemoriesByCategory[category] || []);
}


function findReminiscenceMemory(memoryId) {
    const id = String(memoryId || "");
    return allReminiscenceMemories().find((memory) => String(memory.memory_id) === id)
        || currentReminiscenceSearchResults.find((memory) => String(memory.memory_id) === id)
        || currentReminiscenceAiTopics.find((memory) => String(memory.memory_id) === id)
        || null;
}


function selectDefaultReminiscenceMemory() {
    if (currentSelectedReminiscenceMemoryId && findReminiscenceMemory(currentSelectedReminiscenceMemoryId)) {
        return;
    }
    const firstMemory = allReminiscenceMemories()[0] || currentReminiscenceAiTopics[0] || currentReminiscenceSearchResults[0] || null;
    currentSelectedReminiscenceMemoryId = firstMemory?.memory_id || null;
}


function getReminiscencePatientId() {
    return element("reminiscence-memory-search")?.closest(".reminiscence-memory-shell")?.dataset.patientId
        || currentCaregiverPatientId
        || "demo_patient_001";
}


async function loadReminiscenceMemories() {
    const patientId = getReminiscencePatientId();
    try {
        const response = await fetch(`/api/memories/${encodeURIComponent(patientId)}/by-category`);
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "记忆分类加载失败");
        }
        currentReminiscenceMemoriesByCategory = normalizeReminiscenceGroups(data);
        selectDefaultReminiscenceMemory();
        setReminiscenceStatus("", "neutral");
        renderAll();
    } catch (error) {
        currentReminiscenceMemoriesByCategory = normalizeReminiscenceGroups({});
        setReminiscenceStatus("已确认记忆暂时无法加载，请确认向量库已同步。", "warning");
        renderAll();
        console.error(error);
    }
}


async function loadReminiscenceAiTopics() {
    const patientId = getReminiscencePatientId();
    try {
        const response = await fetch(`/api/memories/search?query=${encodeURIComponent("今天聊什么")}&patient_id=${encodeURIComponent(patientId)}&top_k=3`);
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "推荐话题加载失败");
        }
        currentReminiscenceAiTopics = (Array.isArray(data.results) ? data.results : [])
            .map((item) => normalizeReminiscenceMemory(item, "其他"))
            .filter((item) => item.memory_id && item.text)
            .slice(0, 3);
        selectDefaultReminiscenceMemory();
        renderAll();
    } catch (error) {
        currentReminiscenceAiTopics = [];
        renderAll();
        console.error(error);
    }
}


async function searchReminiscenceMemories(query) {
    const cleanQuery = String(query || "").trim();
    if (!cleanQuery) {
        currentReminiscenceSearchResults = [];
        renderReminiscencePage();
        return;
    }
    const patientId = getReminiscencePatientId();
    try {
        const response = await fetch(`/api/memories/search?query=${encodeURIComponent(cleanQuery)}&patient_id=${encodeURIComponent(patientId)}&top_k=12`);
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "搜索失败");
        }
        currentReminiscenceSearchResults = (Array.isArray(data.results) ? data.results : [])
            .map((item) => {
                const existing = findReminiscenceMemory(item.memory_id);
                return existing ? { ...existing, score: typeof item.score === "number" ? item.score : existing.score } : normalizeReminiscenceMemory(item, "其他");
            })
            .filter((item) => item.memory_id && item.text);
        if (currentReminiscenceSearchResults.length) {
            currentSelectedReminiscenceMemoryId = currentReminiscenceSearchResults[0].memory_id;
        }
        renderReminiscencePage();
    } catch (error) {
        currentReminiscenceSearchResults = [];
        setReminiscenceStatus("搜索暂时不可用，请稍后再试。", "warning");
        renderReminiscencePage();
        console.error(error);
    }
}


function bindReminiscenceSearchInput() {
    const input = element("reminiscence-memory-search");
    if (!input || input.dataset.bound === "true") {
        return;
    }
    input.dataset.bound = "true";
    input.addEventListener("input", () => {
        window.clearTimeout(reminiscenceSearchTimer);
        reminiscenceSearchTimer = window.setTimeout(() => searchReminiscenceMemories(input.value), 250);
    });
}


function reminiscencePromptKeyword(text) {
    const pieces = cleanPieces(text);
    return shortText(pieces[0] || text || "这段回忆", 18);
}


function memoryConversationPrompt(memory) {
    return `你能给我讲讲关于 ${reminiscencePromptKeyword(memory?.text || "")} 的事吗？`;
}


function startConversationWithMemory(memoryId) {
    const memory = findReminiscenceMemory(memoryId);
    if (!memory) {
        return;
    }
    startConversationWithSeed(memoryConversationPrompt(memory));
}


function materialImageUrl(material) {
    return material?.thumbnail_url
        || material?.image_url
        || material?.file_url
        || material?.url
        || material?.file_path
        || "";
}


function findAssociatedPhotoForMemory(memory) {
    const text = String(memory?.text || "");
    return currentFamiliarMaterials.find((material) => {
        if (material.material_type !== "family_photo") {
            return false;
        }
        const imageUrl = materialImageUrl(material);
        if (!imageUrl) {
            return false;
        }
        const candidates = [
            material.related_person,
            material.title,
            material.description,
        ].map((item) => String(item || "").trim()).filter((item) => item.length >= 2);
        return candidates.some((candidate) => text.includes(candidate) || candidate.includes(reminiscencePromptKeyword(text)));
    });
}


function memoryMetaText(memory) {
    const pieces = [];
    if (memory.approved_at) {
        pieces.push(`审批时间：${String(memory.approved_at).replace("T", " ").slice(0, 16)}`);
    }
    if (memory.source) {
        pieces.push(`来源：${shortText(memory.source, 48)}`);
    }
    if (memory.score !== null && memory.score !== undefined) {
        pieces.push(`相关度：${Number(memory.score).toFixed(2)}`);
    }
    return pieces.length ? pieces.join(" · ") : "审批时间和来源暂未记录";
}


function renderReminiscenceMemoryButton(memory) {
    const selected = String(memory.memory_id) === String(currentSelectedReminiscenceMemoryId);
    return `
        <button
            type="button"
            class="reminiscence-memory-item ${selected ? "active" : ""}"
            data-memory-id="${escapeHtml(memory.memory_id)}"
        >
            <span>${escapeHtml(shortText(memory.text, 54))}</span>
            ${memory.score !== null && memory.score !== undefined ? `<small>相关度 ${escapeHtml(Number(memory.score).toFixed(2))}</small>` : ""}
        </button>
    `;
}


function renderReminiscenceCategoryList() {
    const container = element("reminiscence-category-list");
    if (!container) {
        return;
    }
    const query = String(element("reminiscence-memory-search")?.value || "").trim();
    if (query) {
        container.innerHTML = `
            <section class="reminiscence-category-block">
                <h3>搜索结果</h3>
                <div class="reminiscence-memory-items">
                    ${currentReminiscenceSearchResults.length ? currentReminiscenceSearchResults.map(renderReminiscenceMemoryButton).join("") : `
                        <div class="log-empty">
                            <strong>没有匹配的记忆。</strong>
                            <span>可以换一个关键词，或先同步已审批记忆。</span>
                        </div>
                    `}
                </div>
            </section>
        `;
    } else {
        const total = allReminiscenceMemories().length;
        container.innerHTML = total ? reminiscenceCategories.map((category) => {
            const items = currentReminiscenceMemoriesByCategory[category] || [];
            return `
                <section class="reminiscence-category-block">
                    <h3>${escapeHtml(category)} <span>${escapeHtml(String(items.length))}</span></h3>
                    <div class="reminiscence-memory-items">
                        ${items.length ? items.map(renderReminiscenceMemoryButton).join("") : `<p class="reminiscence-empty-category">暂无${escapeHtml(category)}记忆</p>`}
                    </div>
                </section>
            `;
        }).join("") : `
            <div class="log-empty">
                <strong>向量库里还没有已确认记忆。</strong>
                <span>请先运行 scripts/sync_memories.py，或审批新的候选记忆后再同步。</span>
            </div>
        `;
    }

    container.querySelectorAll(".reminiscence-memory-item").forEach((button) => {
        button.addEventListener("click", () => {
            currentSelectedReminiscenceMemoryId = button.dataset.memoryId || "";
            renderReminiscencePage();
        });
    });
}


function renderReminiscenceDetail() {
    const card = element("reminiscence-memory-detail-card");
    if (!card) {
        return;
    }
    const memory = findReminiscenceMemory(currentSelectedReminiscenceMemoryId);
    if (!memory) {
        card.innerHTML = `
            <div class="log-empty">
                <strong>请选择左侧一条记忆。</strong>
                <span>选择后可以查看详情，并用这一段记忆开启对话。</span>
            </div>
        `;
        return;
    }
    const photo = findAssociatedPhotoForMemory(memory);
    const photoUrl = photo ? materialImageUrl(photo) : "";
    card.innerHTML = `
        <div class="reminiscence-detail-text">${escapeHtml(memory.text)}</div>
        ${photoUrl ? `
            <figure class="reminiscence-associated-photo">
                <img src="${escapeHtml(photoUrl)}" alt="${escapeHtml(photo.title || photo.related_person || "关联照片")}">
                <figcaption>${escapeHtml([photo.related_person, photo.title].filter(Boolean).join(" · ") || "关联照片")}</figcaption>
            </figure>
        ` : `
            <div class="reminiscence-no-photo">暂无关联照片，可在熟人素材库补充。</div>
        `}
        <div class="reminiscence-detail-meta">
            <span class="status-pill">${escapeHtml(memory.category || "其他")}</span>
            <span>${escapeHtml(memoryMetaText(memory))}</span>
        </div>
        <button type="button" class="primary-button reminiscence-memory-chat" data-memory-id="${escapeHtml(memory.memory_id)}">🗣️ 用这段记忆开启对话</button>
    `;
    card.querySelector(".reminiscence-memory-chat")?.addEventListener("click", (event) => {
        startConversationWithMemory(event.currentTarget.dataset.memoryId || "");
    });
}


function renderReminiscenceAiTopics() {
    const container = element("reminiscence-ai-topics");
    if (!container) {
        return;
    }
    container.innerHTML = currentReminiscenceAiTopics.length ? currentReminiscenceAiTopics.map((memory, index) => `
        <article class="reminiscence-topic-card">
            <span class="status-pill">话题 ${escapeHtml(String(index + 1))}</span>
            <h3>${escapeHtml(reminiscencePromptKeyword(memory.text))}</h3>
            <p>${escapeHtml(shortText(memory.text, 92))}</p>
            <button type="button" class="ghost-button reminiscence-topic-start" data-memory-id="${escapeHtml(memory.memory_id)}">开启话题</button>
        </article>
    `).join("") : `
        <div class="log-empty">
            <strong>暂时没有推荐话题。</strong>
            <span>同步已审批记忆后，系统会从中挑选 3 个温和话题。</span>
        </div>
    `;
    container.querySelectorAll(".reminiscence-topic-start").forEach((button) => {
        button.addEventListener("click", () => startConversationWithMemory(button.dataset.memoryId || ""));
    });
}


function remindCaregiverName() {
    const primaryLink = currentCaregiverLinks.find((item) => item.is_primary) || currentCaregiverLinks[0];
    if (primaryLink?.caregiver_name) {
        return primaryLink.caregiver_name;
    }
    return currentSelectedPatient.relation || "照护者";
}


function activeReminiscenceMaterials() {
    return currentFamiliarMaterials.filter((material) => material.is_active !== false);
}


function reminiscenceGroupCollections(materials = activeReminiscenceMaterials()) {
    const family = materials.filter((material) => (
        material.material_type === "family_photo"
        || (material.material_type === "voice_message" && Boolean(String(material.related_person || "").trim()))
    ));
    const musicAndVoice = materials.filter((material) => (
        material.material_type === "familiar_music" || material.material_type === "voice_message"
    ));
    const oldPlace = materials.filter((material) => material.material_type === "old_place");
    const oldEvent = materials.filter((material) => material.material_type === "old_event");
    const dailyObject = materials.filter((material) => material.material_type === "daily_object");
    const sensitive = materials.filter((material) => (
        material.material_type === "sensitive_memory" || material.is_sensitive
    ));
    return { family, musicAndVoice, oldPlace, oldEvent, dailyObject, sensitive };
}


function reminiscenceChipDefinitions(materials = activeReminiscenceMaterials()) {
    const groups = reminiscenceGroupCollections(materials);
    return [
        { key: "all", label: "全部", count: materials.length },
        { key: "family", label: "家人", count: groups.family.length },
        { key: "voice_message", label: "语音留言", count: materials.filter((item) => item.material_type === "voice_message").length },
        { key: "familiar_music", label: "老歌", count: materials.filter((item) => item.material_type === "familiar_music").length },
        { key: "old_place", label: "旧地点", count: groups.oldPlace.length },
        { key: "old_event", label: "旧事件", count: groups.oldEvent.length },
        { key: "daily_object", label: "日常物品", count: groups.dailyObject.length },
        { key: "sensitive", label: "敏感内容", count: groups.sensitive.length },
    ];
}


function getActiveReminiscenceFilter() {
    return element("reminiscence-chip-row")?.dataset.activeFilter || "all";
}


function setActiveReminiscenceFilter(filterKey = "all") {
    const row = element("reminiscence-chip-row");
    if (!row) {
        return;
    }
    row.dataset.activeFilter = filterKey;
}


function materialMatchesReminiscenceFilter(material, filterKey) {
    if (filterKey === "all") {
        return true;
    }
    if (filterKey === "family") {
        return material.material_type === "family_photo"
            || (material.material_type === "voice_message" && Boolean(String(material.related_person || "").trim()));
    }
    if (filterKey === "voice_message") {
        return material.material_type === "voice_message";
    }
    if (filterKey === "familiar_music") {
        return material.material_type === "familiar_music";
    }
    if (filterKey === "old_place") {
        return material.material_type === "old_place";
    }
    if (filterKey === "old_event") {
        return material.material_type === "old_event";
    }
    if (filterKey === "daily_object") {
        return material.material_type === "daily_object";
    }
    if (filterKey === "sensitive") {
        return material.material_type === "sensitive_memory" || material.is_sensitive;
    }
    return true;
}


function renderReminiscenceChips(materials = activeReminiscenceMaterials()) {
    const row = element("reminiscence-chip-row");
    if (!row) {
        return;
    }
    const activeFilter = getActiveReminiscenceFilter();
    const chips = reminiscenceChipDefinitions(materials);
    row.innerHTML = chips.map((chip) => `
        <button
            type="button"
            class="reminiscence-chip ${activeFilter === chip.key ? "active" : ""}"
            data-filter="${chip.key}"
        >
            ${escapeHtml(chip.label)} ${escapeHtml(String(chip.count))}
        </button>
    `).join("");
    row.querySelectorAll(".reminiscence-chip").forEach((button) => {
        button.addEventListener("click", () => {
            setActiveReminiscenceFilter(button.dataset.filter || "all");
            renderReminiscencePage();
        });
    });
}


function findReminiscenceStarterMaterials(materials = activeReminiscenceMaterials()) {
    const safeMaterials = materials.filter((material) => !material.is_sensitive && material.material_type !== "sensitive_memory");
    const xiaoyu = safeMaterials.filter((material) => (
        material.material_type === "family_photo"
        || material.material_type === "voice_message"
        || String(material.related_person || "").includes("陈小雨")
        || String(material.title || "").includes("小雨")
    ));
    const music = safeMaterials.filter((material) => material.material_type === "familiar_music");
    const oldStories = safeMaterials.filter((material) => material.material_type === "old_event" || material.material_type === "old_place");
    return { xiaoyu, music, oldStories };
}


function renderReminiscenceRecommended(materials = activeReminiscenceMaterials()) {
    const grid = element("reminiscence-recommended-grid");
    if (!grid) {
        return;
    }
    const starters = findReminiscenceStarterMaterials(materials);
    const cards = [
        {
            title: "和小雨有关",
            prompt: "我想聊聊小雨。",
            buttonLabel: "用这段开始聊天",
            items: starters.xiaoyu,
            empty: "还没有添加相关素材，可到素材库补充。",
        },
        {
            title: "听一首熟悉的老歌",
            prompt: "我想听一首熟悉的老歌。",
            buttonLabel: "想听老歌",
            items: starters.music,
            empty: "还没有添加相关素材，可到素材库补充。",
        },
        {
            title: "想想以前的事",
            prompt: "我想聊聊以前的事情。",
            buttonLabel: "聊聊以前的事",
            items: starters.oldStories,
            empty: "还没有添加相关素材，可到素材库补充。",
        },
    ];
    grid.innerHTML = cards.map((card) => `
        <article class="reminiscence-start-card ${card.items.length ? "ready" : "empty"}">
            <div class="reminiscence-start-card-head">
                <h3>${escapeHtml(card.title)}</h3>
                <span class="status-pill ${card.items.length ? "success" : "neutral"}">${card.items.length ? `${card.items.length} 条素材` : "待补充"}</span>
            </div>
            <p>${escapeHtml(card.items.length ? shortText(card.items.map((item) => item.title || item.description || "").filter(Boolean).join("、"), 70) : card.empty)}</p>
            <div class="reminiscence-actions">
                ${card.items.length ? `
                    <button type="button" class="ghost-button reminiscence-start-chat" data-seed-message="${escapeHtml(card.prompt)}">${escapeHtml(card.buttonLabel)}</button>
                ` : `
                    <a class="ghost-button" href="/materials">去补充素材</a>
                `}
            </div>
        </article>
    `).join("");
    grid.querySelectorAll(".reminiscence-start-chat").forEach((button) => {
        button.addEventListener("click", () => startConversationWithSeed(button.dataset.seedMessage || ""));
    });
}


function materialPromptText(material) {
    return `我想聊聊：${material.title || "这段回忆"}`;
}


function startConversationWithSeed(seedMessage) {
    if (!seedMessage) {
        return;
    }
    const patientPath = currentCaregiverPatientId ? `/${encodeURIComponent(currentCaregiverPatientId)}` : "";
    window.location.href = `/conversation${patientPath}?seed_message=${encodeURIComponent(seedMessage)}`;
}


async function copyReminiscencePrompt(promptText) {
    if (!promptText) {
        return;
    }
    try {
        if (navigator.clipboard?.writeText) {
            await navigator.clipboard.writeText(promptText);
        } else {
            const helper = document.createElement("textarea");
            helper.value = promptText;
            helper.setAttribute("readonly", "true");
            helper.style.position = "absolute";
            helper.style.left = "-9999px";
            document.body.appendChild(helper);
            helper.select();
            document.execCommand("copy");
            document.body.removeChild(helper);
        }
        setReminiscenceStatus("提示语已复制，可以直接发给患者端对话。", "success");
    } catch (error) {
        setReminiscenceStatus("复制失败，请手动复制提示语。", "warning");
        console.error(error);
    }
}


function toggleReminiscenceEscort(materialId) {
    const key = String(materialId || "");
    if (!key) {
        return;
    }
    if (reminiscenceEscortIds.has(key)) {
        reminiscenceEscortIds.delete(key);
        setReminiscenceStatus("已取消“需要家属陪同”提示。", "neutral");
    } else {
        reminiscenceEscortIds.add(key);
        setReminiscenceStatus("已标记为“需要家属陪同”提示。", "warning");
    }
    renderReminiscencePage();
}


function renderReminiscenceCard(material) {
    const prompt = materialPromptText(material);
    const escortMarked = reminiscenceEscortIds.has(String(material.id || ""));
    const useScene = material.use_scene || material.suggested_use_scene || "";
    const activeText = material.is_active === false ? "暂不参与对话" : "可用于对话";
    const safeUrl = shortText(material.url || material.file_path || "", 48);
    return `
        <article class="reminiscence-display-card ${material.is_sensitive ? "reminiscence-display-card-sensitive" : ""}">
            <div class="material-card-pill-row">
                <span class="status-pill">${escapeHtml(materialTypeLabels[material.material_type] || material.material_type || "熟悉素材")}</span>
                <span class="status-pill ${material.is_sensitive ? "warning" : "success"}">${material.is_sensitive ? "敏感" : "非敏感"}</span>
                <span class="status-pill ${material.is_active === false ? "neutral" : "success"}">${escapeHtml(activeText)}</span>
                ${escortMarked ? '<span class="status-pill warning">需要家属陪同</span>' : ""}
            </div>
            <h3>${escapeHtml(material.title || "未命名素材")}</h3>
            <p>${escapeHtml(material.description || "暂无描述。")}</p>
            <div class="reminiscence-card-meta">
                <span><strong>关联人物：</strong>${escapeHtml(material.related_person || "未填写")}</span>
                <span><strong>使用场景：</strong>${escapeHtml(useScene || "未填写")}</span>
                <span><strong>安全提示：</strong>${escapeHtml(material.safety_note || (material.is_sensitive ? "敏感内容不应主动刺激患者。": "暂无额外安全提示"))}</span>
                <span><strong>链接 / 路径：</strong>${escapeHtml(safeUrl || "未填写")}</span>
            </div>
            ${material.is_sensitive ? `
                <div class="reminiscence-sensitive-note">
                    <strong>敏感内容不应主动刺激患者，只在患者主动提及时用于安全安抚。</strong>
                </div>
            ` : ""}
            <div class="reminiscence-actions">
                <button type="button" class="ghost-button reminiscence-material-chat" data-seed-message="${escapeHtml(prompt)}">用这段开始聊天</button>
                <button type="button" class="ghost-button reminiscence-copy-prompt" data-prompt="${escapeHtml(prompt)}">复制提示语</button>
                <a class="ghost-button" href="/materials">编辑素材</a>
                ${material.is_sensitive ? `
                    <button type="button" class="ghost-button reminiscence-escort-toggle" data-material-id="${material.id}">
                        ${escortMarked ? "已标记家属陪同" : "标记为需要家属陪同"}
                    </button>
                ` : ""}
            </div>
        </article>
    `;
}


function buildReminiscenceGroupMarkup(title, description, items, emptyText, options = {}) {
    const { sensitive = false } = options;
    if (sensitive) {
        return `
            <details class="reminiscence-display-group reminiscence-sensitive-group">
                <summary>
                    <div>
                        <h3>${escapeHtml(title)}</h3>
                        <p>${escapeHtml(description)}</p>
                    </div>
                    <span class="status-pill warning">${escapeHtml(String(items.length))} 条</span>
                </summary>
                <div class="reminiscence-display-grid">
                    ${items.length ? items.map(renderReminiscenceCard).join("") : `
                        <div class="log-empty">
                            <strong>${escapeHtml(emptyText)}</strong>
                            <span>如需补充，可到熟悉素材库继续整理。</span>
                        </div>
                    `}
                </div>
            </details>
        `;
    }
    return `
        <section class="reminiscence-display-group">
            <div class="reminiscence-group-head">
                <div>
                    <h3>${escapeHtml(title)}</h3>
                    <p>${escapeHtml(description)}</p>
                </div>
                <span class="status-pill">${escapeHtml(String(items.length))} 条</span>
            </div>
            <div class="reminiscence-display-grid">
                ${items.length ? items.map(renderReminiscenceCard).join("") : `
                    <div class="log-empty">
                        <strong>${escapeHtml(emptyText)}</strong>
                        <span>可以到熟悉素材库补充。</span>
                    </div>
                `}
            </div>
        </section>
    `;
}


function renderReminiscenceGroups(materials = activeReminiscenceMaterials()) {
    const container = element("reminiscence-groups");
    if (!container) {
        return;
    }
    const filterKey = getActiveReminiscenceFilter();
    const groups = reminiscenceGroupCollections(materials);
    const filterItems = (items) => items.filter((material) => materialMatchesReminiscenceFilter(material, filterKey));
    const filteredGroups = {
        family: filterItems(groups.family),
        musicAndVoice: filterItems(groups.musicAndVoice),
        oldPlace: filterItems(groups.oldPlace),
        oldEvent: filterItems(groups.oldEvent),
        dailyObject: filterItems(groups.dailyObject),
        sensitive: filterItems(groups.sensitive),
    };
    const showGroup = (items) => filterKey === "all" || items.length > 0;
    const sections = [];
    if (showGroup(filteredGroups.family)) {
        sections.push(buildReminiscenceGroupMarkup("家人", "更适合用来陪伴认人、想起熟悉关系。", filteredGroups.family, "还没有家人相关素材。"));
    }
    if (showGroup(filteredGroups.musicAndVoice)) {
        sections.push(buildReminiscenceGroupMarkup("老歌与声音", "适合下午焦虑、想听熟悉声音或轻柔陪伴时使用。", filteredGroups.musicAndVoice, "还没有老歌或语音留言素材。"));
    }
    if (showGroup(filteredGroups.oldPlace)) {
        sections.push(buildReminiscenceGroupMarkup("旧地点", "适合从熟悉地方慢慢展开，不追问是否准确。", filteredGroups.oldPlace, "还没有旧地点素材。"));
    }
    if (showGroup(filteredGroups.oldEvent)) {
        sections.push(buildReminiscenceGroupMarkup("旧事件", "适合从过去做过的事、熟悉的工作和日常经历慢慢聊起。", filteredGroups.oldEvent, "还没有旧事件素材。"));
    }
    if (showGroup(filteredGroups.dailyObject)) {
        sections.push(buildReminiscenceGroupMarkup("日常物品", "适合从药盒、杯子、钥匙等熟悉物品开始建立安全感。", filteredGroups.dailyObject, "还没有日常物品素材。"));
    }
    if (showGroup(filteredGroups.sensitive)) {
        sections.push(buildReminiscenceGroupMarkup("敏感内容，需要家属谨慎使用", "默认折叠展示，只在患者主动提及时配合安全安抚使用。", filteredGroups.sensitive, "目前没有敏感素材。", { sensitive: true }));
    }
    container.innerHTML = sections.length ? sections.join("") : `
        <div class="log-empty">
            <strong>当前筛选下没有可展示的素材。</strong>
            <span>可以切换分类，或到熟悉素材库补充更多内容。</span>
        </div>
    `;
    container.querySelectorAll(".reminiscence-material-chat").forEach((button) => {
        button.addEventListener("click", () => startConversationWithSeed(button.dataset.seedMessage || ""));
    });
    container.querySelectorAll(".reminiscence-copy-prompt").forEach((button) => {
        button.addEventListener("click", () => copyReminiscencePrompt(button.dataset.prompt || ""));
    });
    container.querySelectorAll(".reminiscence-escort-toggle").forEach((button) => {
        button.addEventListener("click", () => toggleReminiscenceEscort(button.dataset.materialId || ""));
    });
}


function renderReminiscencePage() {
    selectDefaultReminiscenceMemory();
    const patientName = currentSelectedPatient.name || currentProfile.name || "患者";
    setTextIfPresent("reminiscence-patient-name", `${patientName}的回忆追忆`);
    const patientAge = currentSelectedPatient.age || currentProfile.age || "年龄未填";
    const patientRelation = currentSelectedPatient.relation || currentProfile.hometown || "关系未填";
    setTextIfPresent("reminiscence-profile-line", `${patientAge} 岁 · ${patientRelation} · 选择一条已确认记忆，温和开启陪伴对话。`);
    setTextIfPresent("reminiscence-caregiver-line", `主要家属：${remindCaregiverName()}`);
    bindReminiscenceSearchInput();
    renderReminiscenceCategoryList();
    renderReminiscenceDetail();
    renderReminiscenceAiTopics();
}


function renderMemoryCandidateStatusSummary() {
    const grid = element("analysis-memory-candidate-status-grid");
    if (!grid) {
        return;
    }
    const counts = currentMemoryCandidates.reduce((acc, candidate) => {
        const key = candidate.status || "pending";
        acc[key] = (acc[key] || 0) + 1;
        return acc;
    }, {});
    const rows = [
        ["pending", "待审核", counts.pending || 0],
        ["approved", "已加入", counts.approved || 0],
        ["rejected", "已拒绝", counts.rejected || 0]
    ];
    grid.innerHTML = rows.map(([status, label, value]) => `
        <div class="analysis-status-item ${Number(value) > 0 ? status : "missing"}">
            <span>${escapeHtml(label)}</span>
            <strong>${escapeHtml(String(value))}</strong>
        </div>
    `).join("");
}


function renderRecentChatSummary(logs = currentLogs) {
    const container = element("analysis-recent-chat-list");
    if (!container) {
        return;
    }
    const list = Array.isArray(logs) ? logs : [];
    if (!list.length) {
        container.innerHTML = `
            <div class="log-empty">
                <strong>暂无对话记录。</strong>
                <span>可先进入患者端对话进行测试。</span>
            </div>
        `;
        return;
    }
    const pairs = [];
    for (let index = 0; index < list.length; index += 1) {
        const log = list[index];
        if (log.role !== "user") {
            continue;
        }
        const reply = list.slice(index + 1).find((item) => item.role === "assistant");
        const eventTriggered = currentCaregiverEvents.some((event) => {
            const source = String(event.source_message || "");
            const message = String(log.message || "");
            return source && (source === message || source.includes(message) || message.includes(source));
        });
        pairs.push({ user: log, assistant: reply, eventTriggered });
    }
    const visible = pairs.slice(-5).reverse();
    if (!visible.length) {
        container.innerHTML = `
            <div class="log-empty">
                <strong>暂无对话记录。</strong>
                <span>可先进入患者端对话进行测试。</span>
            </div>
        `;
        return;
    }
    container.innerHTML = visible.map((item) => `
        <article class="analysis-chat-card">
            <time>${escapeHtml(String(item.user.timestamp || "").replace("T", " ").slice(5, 16) || "刚刚")}</time>
            <strong>患者原话：${escapeHtml(item.user.message || "")}</strong>
            <p>系统回复：${escapeHtml(shortText(item.assistant?.message || "暂无回复", 80))}</p>
            <div class="analysis-chat-meta">
                <span>状态/策略：${escapeHtml(item.user.keyword_tags || item.assistant?.keyword_tags || "暂无")}</span>
                <span>${item.eventTriggered ? "已触发家属事件" : "未触发家属事件"}</span>
            </div>
        </article>
    `).join("");
}


function clearMaterialForm() {
    [
        "material-id",
        "material-title",
        "material-description",
        "material-related-person",
        "material-file-path",
        "material-thumbnail-url",
        "material-transcript-text",
        "material-artist",
        "material-use-scene",
        "material-suggested-use-scene",
        "material-related-time",
        "material-photo-year",
        "material-tags",
        "material-story-text",
        "material-safety-note"
    ].forEach((id) => {
        const node = element(id);
        if (node) {
            node.value = "";
        }
    });
    if (element("material-type")) {
        element("material-type").value = "family_photo";
    }
    if (element("material-is-sensitive")) {
        element("material-is-sensitive").checked = false;
    }
    if (element("material-is-active")) {
        element("material-is-active").checked = true;
    }
    if (element("material-sensitivity-level")) {
        element("material-sensitivity-level").value = "";
    }
    setMaterialFormMode(false);
    updateMaterialTypeHints();
    setMaterialFormStatus("准备就绪", "neutral");
}


function materialPayloadFromForm() {
    return {
        material_type: element("material-type")?.value || "old_event",
        title: element("material-title")?.value.trim() || "",
        description: element("material-description")?.value.trim() || "",
        related_person: element("material-related-person")?.value.trim() || "",
        file_path: element("material-file-path")?.value.trim() || "",
        thumbnail_url: element("material-thumbnail-url")?.value.trim() || "",
        transcript_text: element("material-transcript-text")?.value.trim() || "",
        artist: element("material-artist")?.value.trim() || "",
        use_scene: element("material-use-scene")?.value.trim() || "",
        suggested_use_scene: element("material-suggested-use-scene")?.value.trim() || "",
        related_time: element("material-related-time")?.value.trim() || "",
        photo_year: element("material-photo-year")?.value ? Number(element("material-photo-year").value) : null,
        sensitivity_level: element("material-sensitivity-level")?.value || "",
        tags: element("material-tags")?.value.trim() || "",
        story_text: element("material-story-text")?.value.trim() || "",
        safety_note: element("material-safety-note")?.value.trim() || "",
        is_sensitive: Boolean(element("material-is-sensitive")?.checked),
        is_active: Boolean(element("material-is-active")?.checked ?? true)
    };
}


function materialPayloadFromMaterial(material, overrides = {}) {
    if (!material) {
        return overrides;
    }
    return {
        material_type: material.material_type || "old_event",
        title: material.title || "",
        description: material.description || "",
        related_person: material.related_person || "",
        file_path: material.file_path || material.url || "",
        thumbnail_url: material.thumbnail_url || material.image_url || "",
        transcript_text: material.transcript_text || "",
        artist: material.artist || "",
        use_scene: material.use_scene || "",
        suggested_use_scene: material.suggested_use_scene || "",
        related_time: material.related_time || "",
        photo_year: material.photo_year || null,
        photo_decade: material.photo_decade || "",
        sensitivity_level: material.sensitivity_level || "",
        tags: material.tags || "",
        story_text: material.story_text || "",
        voice_note_path: material.voice_note_path || "",
        safety_note: material.safety_note || "",
        is_sensitive: Boolean(material.is_sensitive),
        is_active: material.is_active !== false,
        ...overrides,
    };
}


function setMaterialFormMode(isEditing) {
    setTextIfPresent("materials-form-title", isEditing ? "编辑熟悉素材" : "添加熟悉素材");
    const saveButton = element("material-save-button");
    if (saveButton) {
        saveButton.textContent = isEditing ? "保存修改" : "保存素材";
    }
}


function setMaterialFormStatus(message, kind = "neutral") {
    const node = element("material-form-status");
    if (!node) {
        return;
    }
    node.textContent = message;
    node.className = `status-pill ${kind}`;
}


function updateMaterialTypeHints() {
    const type = element("material-type")?.value || "family_photo";
    const hint = materialTypeFormHints[type] || materialTypeFormHints.family_photo;
    setTextIfPresent("materials-type-helper", hint.helper || "");
    const filePath = element("material-file-path");
    const thumbnail = element("material-thumbnail-url");
    const transcript = element("material-transcript-text");
    const artist = element("material-artist");
    const useScene = element("material-use-scene");
    if (filePath) {
        filePath.placeholder = hint.filePath || filePath.placeholder;
    }
    if (thumbnail) {
        thumbnail.placeholder = hint.thumbnail || thumbnail.placeholder;
    }
    if (transcript) {
        transcript.placeholder = hint.transcript || transcript.placeholder;
    }
    if (artist) {
        artist.placeholder = hint.artist || artist.placeholder;
    }
    if (useScene) {
        useScene.placeholder = hint.useScene || useScene.placeholder;
    }
}


function fillMaterialForm(material) {
    if (!material) {
        clearMaterialForm();
        return;
    }
    element("material-id").value = String(material.id || "");
    element("material-type").value = material.material_type || "old_event";
    element("material-title").value = material.title || "";
    element("material-description").value = material.description || "";
    element("material-related-person").value = material.related_person || "";
    element("material-file-path").value = material.file_path || material.url || "";
    element("material-thumbnail-url").value = material.thumbnail_url || material.image_url || "";
    element("material-transcript-text").value = material.transcript_text || "";
    element("material-artist").value = material.artist || "";
    element("material-use-scene").value = material.use_scene || "";
    element("material-suggested-use-scene").value = material.suggested_use_scene || "";
    element("material-related-time").value = material.related_time || "";
    element("material-photo-year").value = material.photo_year || "";
    element("material-sensitivity-level").value = material.sensitivity_level || "";
    element("material-tags").value = materialTags(material).join(", ");
    element("material-story-text").value = material.story_text || "";
    element("material-safety-note").value = material.safety_note || "";
    element("material-is-sensitive").checked = Boolean(material.is_sensitive);
    element("material-is-active").checked = material.is_active !== false;
    setMaterialFormMode(true);
    updateMaterialTypeHints();
    setMaterialFormStatus("正在编辑素材", "warning");
    openMaterialsDrawer();
}


async function saveMaterial() {
    if (!currentUserId) {
        setMaterialFormStatus("没有患者资料", "warning");
        return;
    }
    const materialId = element("material-id")?.value.trim();
    const payload = materialPayloadFromForm();
    if (!payload.title) {
        setMaterialFormStatus("请填写标题", "warning");
        return;
    }
    if (payload.material_type === "sensitive_memory" && !payload.safety_note) {
        setMaterialFormStatus("敏感记忆请填写安全提示", "warning");
        return;
    }
    const url = materialId
        ? `/api/materials/${encodeURIComponent(currentUserId)}/${encodeURIComponent(materialId)}`
        : `/api/materials/${encodeURIComponent(currentUserId)}`;
    const method = materialId ? "PUT" : "POST";
    const saveButton = element("material-save-button");
    const resetButton = element("material-reset-button");
    const originalText = saveButton?.textContent || "";
    try {
        if (saveButton) {
            saveButton.disabled = true;
            saveButton.textContent = materialId ? "保存中" : "添加中";
        }
        if (resetButton) {
            resetButton.disabled = true;
        }
        setMaterialFormStatus(materialId ? "正在保存修改..." : "正在添加素材...", "warning");
        const response = await fetch(url, {
            method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "保存失败");
        }
        currentFamiliarMaterials = Array.isArray(data.materials) ? [...data.materials] : currentFamiliarMaterials;
        currentFamiliarMaterialStatus = data.material_status ? { ...data.material_status } : currentFamiliarMaterialStatus;
        clearMaterialForm();
        renderMaterialsPage();
        setMaterialFormStatus(materialId ? "素材修改已保存。" : "素材已添加。", "success");
    } catch (error) {
        setMaterialFormStatus(error.message || "保存失败，请稍后再试。", "warning");
        console.error(error);
    } finally {
        if (saveButton) {
            saveButton.disabled = false;
            saveButton.textContent = originalText || (materialId ? "保存修改" : "保存素材");
        }
        if (resetButton) {
            resetButton.disabled = false;
        }
    }
}


async function deleteMaterial(materialId) {
    if (!currentUserId || !materialId) {
        return;
    }
    if (!window.confirm("确定删除这条熟悉素材吗？")) {
        return;
    }
    try {
        const response = await fetch(`/api/materials/${encodeURIComponent(currentUserId)}/${encodeURIComponent(materialId)}`, {
            method: "DELETE"
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "删除失败");
        }
        currentFamiliarMaterials = Array.isArray(data.materials) ? [...data.materials] : [];
        currentFamiliarMaterialStatus = data.material_status ? { ...data.material_status } : {};
        clearMaterialForm();
        renderMaterialsPage();
        setMaterialFormStatus("素材已删除。", "success");
    } catch (error) {
        setMaterialFormStatus(error.message || "删除失败，请稍后再试。", "warning");
        console.error(error);
    }
}


async function updateMaterialQuickFlag(materialId, overrides, successText) {
    if (!currentUserId || !materialId) {
        return;
    }
    const material = currentFamiliarMaterials.find((item) => String(item.id) === String(materialId));
    if (!material) {
        return;
    }
    try {
        const response = await fetch(`/api/materials/${encodeURIComponent(currentUserId)}/${encodeURIComponent(materialId)}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(materialPayloadFromMaterial(material, overrides))
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "更新失败");
        }
        currentFamiliarMaterials = Array.isArray(data.materials) ? [...data.materials] : currentFamiliarMaterials;
        currentFamiliarMaterialStatus = data.material_status ? { ...data.material_status } : currentFamiliarMaterialStatus;
        renderMaterialsPage();
        setMaterialFormStatus(successText, "success");
    } catch (error) {
        setMaterialFormStatus(error.message || "更新失败，请稍后再试。", "warning");
        console.error(error);
    }
}


function stopMaterialVoiceRecording() {
    if (materialVoiceRecorder && materialVoiceRecorder.state !== "inactive") {
        materialVoiceRecorder.stop();
    }
}


async function recordMaterialVoiceNote(materialId) {
    if (!materialId) {
        return;
    }
    if (materialVoiceRecorder && materialVoiceRecorder.state === "recording") {
        stopMaterialVoiceRecording();
        return;
    }
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
        setMaterialFormStatus("当前浏览器不支持录音。", "warning");
        return;
    }
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        materialVoiceChunks = [];
        materialVoiceRecordingId = String(materialId);
        materialVoiceRecorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
        materialVoiceRecorder.ondataavailable = (event) => {
            if (event.data && event.data.size > 0) {
                materialVoiceChunks.push(event.data);
            }
        };
        materialVoiceRecorder.onstop = async () => {
            stream.getTracks().forEach((track) => track.stop());
            window.clearTimeout(materialVoiceStopTimer);
            const blob = new Blob(materialVoiceChunks, { type: "audio/webm" });
            materialVoiceChunks = [];
            const recordingId = materialVoiceRecordingId;
            materialVoiceRecordingId = null;
            renderMaterialsPage();
            if (!blob.size || !recordingId) {
                setMaterialFormStatus("没有录到声音，请重新录制。", "warning");
                return;
            }
            const formData = new FormData();
            formData.append("audio", blob, `material_${recordingId}.webm`);
            try {
                setMaterialFormStatus("正在上传语音说明...", "warning");
                const response = await fetch(`/api/materials/${encodeURIComponent(recordingId)}/voice-note`, {
                    method: "POST",
                    body: formData
                });
                const data = await response.json();
                if (!response.ok) {
                    throw new Error(data.detail || "上传失败");
                }
                const updated = data.material || null;
                if (updated) {
                    currentFamiliarMaterials = currentFamiliarMaterials.map((item) => (
                        String(item.id) === String(updated.id) ? updated : item
                    ));
                    renderMaterialsPage();
                }
                setMaterialFormStatus("语音说明已保存。", "success");
            } catch (error) {
                setMaterialFormStatus(error.message || "语音说明上传失败。", "warning");
            }
        };
        materialVoiceRecorder.start();
        materialVoiceStopTimer = window.setTimeout(stopMaterialVoiceRecording, 60000);
        setMaterialFormStatus("正在录制语音说明，再点一次停止，最长 60 秒。", "warning");
        renderMaterialsPage();
    } catch (error) {
        setMaterialFormStatus("无法开启麦克风，请检查浏览器权限。", "warning");
    }
}


function bindMaterialsPage() {
    element("material-save-button")?.addEventListener("click", saveMaterial);
    element("material-reset-button")?.addEventListener("click", clearMaterialForm);
    element("materials-drawer-open-button")?.addEventListener("click", () => {
        clearMaterialForm();
        openMaterialsDrawer();
    });
    element("materials-drawer-close-button")?.addEventListener("click", closeMaterialsDrawer);
    element("material-type")?.addEventListener("change", updateMaterialTypeHints);
    ["materials-filter-type", "materials-filter-sensitive", "materials-filter-search", "materials-filter-active"].forEach((id) => {
        element(id)?.addEventListener("input", renderMaterialsPage);
        element(id)?.addEventListener("change", renderMaterialsPage);
    });
    updateMaterialTypeHints();
}


function openMaterialsDrawer() {
    document.body.classList.add("materials-drawer-open");
}


function closeMaterialsDrawer() {
    document.body.classList.remove("materials-drawer-open");
}


function getFilteredMaterials() {
    const typeFilter = element("materials-filter-type")?.value || "";
    const sensitiveFilter = element("materials-filter-sensitive")?.value || "";
    const activeFilter = element("materials-filter-active")?.value || "";
    const search = String(element("materials-filter-search")?.value || "").trim().toLowerCase();
    return currentFamiliarMaterials.filter((material) => {
        if (typeFilter && material.material_type !== typeFilter) {
            return false;
        }
        if (sensitiveFilter === "sensitive" && !material.is_sensitive) {
            return false;
        }
        if (sensitiveFilter === "normal" && material.is_sensitive) {
            return false;
        }
        if (activeFilter === "active" && material.is_active === false) {
            return false;
        }
        if (activeFilter === "inactive" && material.is_active !== false) {
            return false;
        }
        if (!search) {
            return true;
        }
        const haystack = [
            material.title,
            material.description,
            material.related_person,
            material.tags,
            material.transcript_text,
            material.artist
        ].join(" ").toLowerCase();
        return haystack.includes(search);
    });
}


function renderMaterialsOverview() {
    const grid = element("materials-overview-grid");
    if (!grid) {
        return;
    }
    const counts = currentFamiliarMaterials.reduce((acc, material) => {
        const key = material.material_type || "old_event";
        acc[key] = (acc[key] || 0) + 1;
        acc.total = (acc.total || 0) + 1;
        return acc;
    }, {});
    const rows = [
        ["全部素材数量", counts.total || 0],
        ["家人照片数量", counts.family_photo || 0],
        ["语音留言数量", counts.voice_message || 0],
        ["熟悉音乐数量", counts.familiar_music || 0],
        ["旧地点数量", counts.old_place || 0],
        ["旧事件数量", counts.old_event || 0],
        ["敏感记忆数量", counts.sensitive_memory || 0],
    ];
    grid.innerHTML = rows.map(([label, value]) => `
        <div class="materials-overview-item ${Number(value) > 0 ? "ready" : "missing"}">
            <span>${escapeHtml(label)}</span>
            <strong>${escapeHtml(String(value))}</strong>
        </div>
    `).join("");
}


function materialMetaLines(material) {
    return [
        material.related_person && `关联人物：${material.related_person}`,
        (material.use_scene || material.suggested_use_scene) && `使用场景：${material.use_scene || material.suggested_use_scene}`,
        material.related_time && `相关时间：${material.related_time}`,
        material.photo_year && `照片年份：${material.photo_year}`,
        material.artist && `艺术家：${material.artist}`,
        material.sensitivity_level && `敏感等级：${material.sensitivity_level}`,
    ].filter(Boolean);
}


function materialLinkText(material) {
    return shortText(material.file_path || material.url || material.image_url || material.audio_url || material.music_url || "", 72);
}


function materialImageUrl(material) {
    const candidate = material.thumbnail_url || material.image_url || material.file_path || material.url || "";
    return /^(https?:\/\/|\/static\/|data:image\/)/.test(String(candidate)) ? String(candidate) : "";
}


function materialTags(material) {
    if (Array.isArray(material?.tag_list)) {
        return material.tag_list.map((tag) => String(tag).trim()).filter(Boolean);
    }
    const raw = String(material?.tags || "").trim();
    if (!raw) {
        return [];
    }
    if (raw.startsWith("[")) {
        try {
            const parsed = JSON.parse(raw);
            if (Array.isArray(parsed)) {
                return parsed.map((tag) => String(tag).trim()).filter(Boolean);
            }
        } catch (error) {
            // 历史脏数据按逗号标签兜底展示。
        }
    }
    return raw.split(/[,，]/).map((tag) => tag.trim()).filter(Boolean);
}


function materialRelationshipLabel(material) {
    const tags = materialTags(material);
    return material.related_person || tags[0] || materialTypeLabels[material.material_type] || "熟悉素材";
}


function renderMaterialsPage() {
    renderMaterialsOverview();
    const countNode = element("materials-count");
    if (countNode) {
        countNode.textContent = `${getFilteredMaterials().length} / ${currentFamiliarMaterials.length} 条`;
    }
    const list = element("materials-list");
    if (!list) {
        return;
    }
    const visibleMaterials = getFilteredMaterials();
    if (!visibleMaterials.length) {
        list.innerHTML = `
            <div class="log-empty">
                <strong>没有匹配的熟悉素材。</strong>
                <span>可以调整筛选，或先添加小雨照片、语音留言、老歌、温州菜场或服装厂经历。</span>
            </div>
        `;
        return;
    }
    list.innerHTML = visibleMaterials.map((material) => `
        <article class="material-card material-photo-card ${material.is_sensitive ? "material-card-sensitive" : ""}">
            <div class="material-photo-frame">
                ${materialImageUrl(material)
                    ? `<img src="${escapeHtml(materialImageUrl(material))}" alt="${escapeHtml(material.title || "熟悉照片")}">`
                    : `<div class="material-photo-placeholder" aria-hidden="true">${escapeHtml((material.title || material.related_person || "素").slice(0, 1))}</div>`}
                <div class="material-photo-overlay">查看详情</div>
            </div>
            <div class="material-card-main">
                <div class="material-card-pill-row">
                    <span class="status-pill">${escapeHtml(materialTypeLabels[material.material_type] || material.material_type)}</span>
                    ${material.is_sensitive ? '<span class="status-pill warning">敏感</span>' : '<span class="status-pill success">非敏感</span>'}
                    ${material.is_active === false ? '<span class="status-pill neutral">不参与对话</span>' : '<span class="status-pill success">可用于对话</span>'}
                </div>
                <h3>${escapeHtml(material.title || "未命名素材")}</h3>
                <span class="material-relation-badge">${escapeHtml(materialRelationshipLabel(material))}</span>
                <p>${escapeHtml(material.description || "暂无描述。")}</p>
                <div class="material-card-meta">
                    ${materialMetaLines(material).length ? materialMetaLines(material).map((line) => `<span>${escapeHtml(line)}</span>`).join("") : '<span>未填写更多线索</span>'}
                </div>
                ${materialTags(material).length ? `<div class="material-tag-row">${materialTags(material).map((tag) => `<span class="app-inline-pill">${escapeHtml(tag)}</span>`).join("")}</div>` : ""}
                ${materialLinkText(material) ? `<small>链接 / 路径：${escapeHtml(materialLinkText(material))}</small>` : ""}
                ${material.story_text ? `<p class="material-story-preview">照片故事：${escapeHtml(material.story_text)}</p>` : ""}
                ${material.transcript_text ? `<p class="material-safety-note">转写摘要：${escapeHtml(material.transcript_text)}</p>` : ""}
                ${material.safety_note ? `<p class="material-safety-note">安全提示：${escapeHtml(material.safety_note)}</p>` : ""}
                ${material.is_sensitive ? '<p class="material-sensitive-tip">敏感素材不会主动刺激患者，只有相关话题被触发时才用于安全模板。</p>' : ""}
            </div>
            <div class="material-card-actions">
                <button type="button" class="ghost-button material-chat-button" data-material-title="${escapeHtml(material.title || "熟悉素材")}">用这段开始聊天</button>
                <button type="button" class="ghost-button material-voice-record-button ${String(materialVoiceRecordingId) === String(material.id) ? "recording" : ""}" data-material-id="${material.id}">${String(materialVoiceRecordingId) === String(material.id) ? "停止录音" : "🎙️ 录制语音说明"}</button>
                ${material.voice_note_path ? `<button type="button" class="ghost-button material-voice-play-button" data-voice-path="${escapeHtml(material.voice_note_path)}">🔊 播放说明</button>` : ""}
                <button type="button" class="ghost-button material-edit-button" data-material-id="${material.id}">编辑</button>
                ${material.material_type === "sensitive_memory"
                    ? '<span class="status-pill warning">敏感类型</span>'
                    : `<button type="button" class="ghost-button material-sensitive-toggle" data-material-id="${material.id}" data-next-sensitive="${material.is_sensitive ? "false" : "true"}">${material.is_sensitive ? "取消敏感" : "标记敏感"}</button>`}
                <button type="button" class="ghost-button material-active-toggle" data-material-id="${material.id}" data-next-active="${material.is_active === false ? "true" : "false"}">${material.is_active === false ? "启用" : "停用"}</button>
                <button type="button" class="ghost-button material-delete-button" data-material-id="${material.id}">删除</button>
            </div>
        </article>
    `).join("");
    list.querySelectorAll(".material-chat-button").forEach((button) => {
        button.addEventListener("click", () => {
            const title = button.dataset.materialTitle || "熟悉素材";
            window.location.href = `/conversation?seed_message=${encodeURIComponent(`我想聊聊：${title}`)}`;
        });
    });
    list.querySelectorAll(".material-voice-record-button").forEach((button) => {
        button.addEventListener("click", () => recordMaterialVoiceNote(button.dataset.materialId));
    });
    list.querySelectorAll(".material-voice-play-button").forEach((button) => {
        button.addEventListener("click", () => {
            const path = button.dataset.voicePath || "";
            if (path) {
                new Audio(path).play().catch(() => setMaterialFormStatus("语音说明播放失败。", "warning"));
            }
        });
    });
    list.querySelectorAll(".material-edit-button").forEach((button) => {
        button.addEventListener("click", () => {
            const material = currentFamiliarMaterials.find((item) => String(item.id) === String(button.dataset.materialId));
            fillMaterialForm(material);
            element("material-title")?.focus();
        });
    });
    list.querySelectorAll(".material-sensitive-toggle").forEach((button) => {
        button.addEventListener("click", () => {
            const nextSensitive = button.dataset.nextSensitive === "true";
            updateMaterialQuickFlag(
                button.dataset.materialId,
                {
                    is_sensitive: nextSensitive,
                    sensitivity_level: nextSensitive ? "high" : "",
                },
                nextSensitive ? "素材已标记为敏感。" : "素材已取消敏感标记。"
            );
        });
    });
    list.querySelectorAll(".material-active-toggle").forEach((button) => {
        button.addEventListener("click", () => {
            const nextActive = button.dataset.nextActive === "true";
            updateMaterialQuickFlag(
                button.dataset.materialId,
                { is_active: nextActive },
                nextActive ? "素材已启用，可进入对话。" : "素材已停用，不再进入对话。"
            );
        });
    });
    list.querySelectorAll(".material-delete-button").forEach((button) => {
        button.addEventListener("click", () => deleteMaterial(button.dataset.materialId));
    });
}


function setChatHistoryStatus(message, kind = "neutral") {
    const node = element("chat-history-candidate-status");
    if (!node) {
        return;
    }
    if (!message) {
        node.textContent = "";
        node.className = "materials-form-status materials-form-status-hidden";
        return;
    }
    node.textContent = message;
    node.className = `materials-form-status materials-form-status-${kind}`;
}


function normalizeChatHistoryText(text) {
    return String(text || "")
        .toLowerCase()
        .replace(/\s+/g, "")
        .replace(/[，。！？、,.!?；;：:“”"'‘’（）()【】\[\]\-]/g, "");
}


function formatHistoryDateTime(timestamp) {
    const value = String(timestamp || "");
    if (!value) {
        return "未记录时间";
    }
    const parts = value.split("T");
    if (parts.length === 2) {
        return `${parts[0]} ${parts[1].slice(0, 5)}`;
    }
    return value.replace(" ", " ").slice(0, 16);
}


function splitKeywordTags(keywordTags) {
    return String(keywordTags || "")
        .split(",")
        .map((tag) => tag.trim())
        .filter(Boolean);
}


function parseTimestampToTime(timestamp) {
    const value = String(timestamp || "");
    if (!value) {
        return 0;
    }
    const normalized = value.includes("T") ? value : value.replace(" ", "T");
    const millis = Date.parse(normalized);
    return Number.isNaN(millis) ? 0 : millis;
}


function getPrimaryCaregiverName() {
    const primaryLink = currentCaregiverLinks.find((item) => item.is_primary) || currentCaregiverLinks[0];
    if (primaryLink?.caregiver_name) {
        return primaryLink.caregiver_name;
    }
    return currentSelectedPatient.relation || "照护者";
}


function messageTouchesFamiliarMaterials(message) {
    const normalizedMessage = normalizeChatHistoryText(message);
    if (!normalizedMessage) {
        return false;
    }
    return currentFamiliarMaterials.some((material) => {
        const checks = [
            material.title,
            material.description,
            material.related_person,
            material.artist,
            material.tags,
        ];
        return checks.some((value) => {
            const normalizedValue = normalizeChatHistoryText(value);
            return normalizedValue && normalizedMessage.includes(normalizedValue.slice(0, Math.min(normalizedValue.length, 8)));
        });
    });
}


function detectChatHistoryCategory(message, matchedEvents = [], candidate = null, repeatedFlag = false) {
    const text = String(message || "");
    if (repeatedFlag) {
        return "repeated_question";
    }
    const eventTypes = matchedEvents.map((item) => item.event_type);
    if (eventTypes.includes("medication_uncertainty")) {
        return "medication_uncertainty";
    }
    if (eventTypes.includes("anxiety")) {
        return "anxiety";
    }
    if (eventTypes.includes("disorientation") || eventTypes.includes("date_time_confusion")) {
        return "disorientation";
    }
    if (eventTypes.includes("wandering_intent")) {
        return "wandering_intent";
    }
    if (eventTypes.includes("sensitive_deceased_spouse_topic")) {
        return "sensitive_deceased_spouse_topic";
    }
    if (candidate || /以前|年轻|做衣服|服装厂|老歌|菜场|温州|小时候/.test(text)) {
        return "reminiscence_content";
    }
    if (/吃药|药盒|降压药|药/.test(text)) {
        return "medication_uncertainty";
    }
    if (/害怕|不安|紧张|别丢下我|没人管/.test(text)) {
        return "anxiety";
    }
    if (/这里是哪里|今天几号|几点了|我在哪/.test(text)) {
        return "disorientation";
    }
    if (/出去走走|回家|出门/.test(text)) {
        return "wandering_intent";
    }
    if (/老王|王建国|老伴/.test(text)) {
        return "sensitive_deceased_spouse_topic";
    }
    return "normal";
}


function buildChatHistoryEntries() {
    const logs = Array.isArray(currentLogs) ? [...currentLogs] : [];
    const sortedLogs = logs.sort((left, right) => parseTimestampToTime(left.timestamp) - parseTimestampToTime(right.timestamp));
    const candidateByMessage = new Map(
        currentMemoryCandidates.map((candidate) => [normalizeChatHistoryText(candidate.source_message), candidate])
    );

    return sortedLogs.reduce((entries, log, index) => {
        if (log.role !== "user") {
            return entries;
        }
        let assistantReply = "";
        for (let cursor = index + 1; cursor < sortedLogs.length; cursor += 1) {
            if (sortedLogs[cursor].role === "assistant") {
                assistantReply = sortedLogs[cursor].message || "";
                break;
            }
            if (sortedLogs[cursor].role === "user") {
                break;
            }
        }

        const normalizedMessage = normalizeChatHistoryText(log.message);
        const matchedEvents = currentCaregiverEvents.filter((event) => normalizeChatHistoryText(event.source_message) === normalizedMessage);
        const matchedCandidate = candidateByMessage.get(normalizedMessage) || null;
        const category = detectChatHistoryCategory(log.message, matchedEvents, matchedCandidate, Boolean(log.repeated_flag));
        const keywordTags = splitKeywordTags(log.keyword_tags);
        const usesReminderStatus = category === "medication_uncertainty" || matchedEvents.some((item) => item.event_type === "medication_uncertainty");
        const usesFamiliarMaterials = messageTouchesFamiliarMaterials(log.message) || category === "reminiscence_content";

        entries.push({
            id: log.id || `chat-${index}`,
            timestamp: log.timestamp || "",
            timeLabel: formatHistoryDateTime(log.timestamp),
            patientMessage: log.message || "",
            assistantReply,
            category,
            categoryLabel: chatHistoryCategoryLabels[category] || "普通聊天",
            detectedState: chatHistoryDetectedStateLabels[category] || "",
            strategy: chatHistoryStrategyLabels[category] || "",
            hasCaregiverEvent: matchedEvents.length > 0,
            caregiverEvents: matchedEvents,
            usesReminderStatus,
            usesFamiliarMaterials,
            candidate: matchedCandidate,
            canBecomeCandidate: Boolean(matchedCandidate) || category === "reminiscence_content",
            keywordTags,
            searchText: [
                log.message,
                assistantReply,
                keywordTags.join(" "),
                chatHistoryCategoryLabels[category] || "",
                matchedEvents.map((item) => eventTypeLabels[item.event_type] || item.event_type).join(" "),
            ].join(" ").toLowerCase(),
        });
        return entries;
    }, []).reverse();
}


function renderChatHistoryOverview(entries) {
    const patientName = currentSelectedPatient.name || currentProfile.name || "患者";
    setTextIfPresent("chat-history-patient-name", patientName);
    setTextIfPresent("chat-history-caregiver-name", `主要家属：${getPrimaryCaregiverName()}`);

    const grid = element("chat-history-stats-grid");
    if (!grid) {
        return;
    }
    const riskCount = entries.filter((entry) => entry.hasCaregiverEvent || entry.category !== "normal").length;
    const candidateCounts = currentMemoryCandidates.reduce((acc, candidate) => {
        const key = candidate.status || "pending";
        acc[key] = (acc[key] || 0) + 1;
        return acc;
    }, {});
    const rows = [
        ["ready", "最近聊天数量", entries.length],
        ["warning", "风险相关对话数量", riskCount],
        ["pending", "待审核候选", candidateCounts.pending || 0],
        ["approved", "已加入素材", candidateCounts.approved || 0],
        ["rejected", "已忽略", candidateCounts.rejected || 0],
    ];
    grid.innerHTML = rows.map(([kind, label, value]) => `
        <div class="analysis-status-item ${kind}">
            <span>${escapeHtml(label)}</span>
            <strong>${escapeHtml(String(value))}</strong>
        </div>
    `).join("");
}


function filterChatHistoryEntries(entries) {
    const searchText = String(element("chat-history-search")?.value || "").trim().toLowerCase();
    const typeFilter = element("chat-history-type-filter")?.value || "all";
    const dateFilter = element("chat-history-date-filter")?.value || "today";
    const eventFilter = element("chat-history-event-filter")?.value || "all";
    const now = Date.now();

    return entries.filter((entry) => {
        if (searchText && !entry.searchText.includes(searchText)) {
            return false;
        }
        if (typeFilter !== "all" && entry.category !== typeFilter) {
            return false;
        }
        if (eventFilter === "triggered" && !entry.hasCaregiverEvent) {
            return false;
        }
        if (eventFilter === "not_triggered" && entry.hasCaregiverEvent) {
            return false;
        }

        const entryTime = parseTimestampToTime(entry.timestamp);
        if (dateFilter === "today" && entryTime) {
            const entryDate = new Date(entryTime);
            const today = new Date(now);
            if (formatDateKey(entryDate) !== formatDateKey(today)) {
                return false;
            }
        }
        if (dateFilter === "3d" && entryTime && now - entryTime > 3 * 24 * 60 * 60 * 1000) {
            return false;
        }
        if (dateFilter === "7d" && entryTime && now - entryTime > 7 * 24 * 60 * 60 * 1000) {
            return false;
        }
        return true;
    });
}


function renderChatHistoryEntries(entries) {
    const container = element("chat-history-log-list");
    const countNode = element("chat-history-log-count");
    if (!container) {
        return;
    }

    if (countNode) {
        countNode.textContent = `${entries.length} 条`;
    }

    if (!entries.length) {
        container.innerHTML = `
            <div class="log-empty">
                <strong>暂无聊天记录。可以先到患者端测试几句典型场景。</strong>
                <span>建议试试：“我是不是还没吃药？”、“我要回家”、“我以前是不是在服装厂做过衣服？”</span>
                <a class="ghost-button" href="/conversation?debug=1">进入患者端对话</a>
            </div>
        `;
        return;
    }

    container.innerHTML = entries.map((entry) => `
        <article class="chat-history-entry-card ${entry.hasCaregiverEvent ? "chat-history-entry-risk" : ""}">
            <div class="chat-history-entry-head">
                <div>
                    <p class="chat-history-entry-time">${escapeHtml(entry.timeLabel)}</p>
                    <h3>${escapeHtml(entry.categoryLabel)}</h3>
                </div>
                <div class="history-tag-row">
                    <span class="status-pill">${escapeHtml(entry.categoryLabel)}</span>
                    ${entry.hasCaregiverEvent ? '<span class="status-pill warning">已触发家属事件</span>' : '<span class="status-pill neutral">未触发家属事件</span>'}
                    ${entry.usesReminderStatus ? '<span class="status-pill warning">涉及 reminder_status</span>' : ""}
                    ${entry.usesFamiliarMaterials ? '<span class="status-pill success">涉及熟悉素材</span>' : ""}
                    ${entry.canBecomeCandidate ? '<span class="status-pill pending">可沉淀为记忆候选</span>' : ""}
                </div>
            </div>
            <div class="chat-history-entry-body">
                <div class="chat-history-entry-message">
                    <span>患者原话</span>
                    <p>${escapeHtml(entry.patientMessage || "暂无内容")}</p>
                </div>
                <div class="chat-history-entry-message">
                    <span>系统最终回复摘要</span>
                    <p>${escapeHtml(shortText(entry.assistantReply || "暂无回复记录。", 100) || "暂无回复记录。")}</p>
                </div>
            </div>
            <div class="chat-history-entry-meta">
                ${entry.detectedState ? `<span><strong>detected_state：</strong>${escapeHtml(entry.detectedState)}</span>` : ""}
                ${entry.strategy ? `<span><strong>strategy：</strong>${escapeHtml(entry.strategy)}</span>` : ""}
                <span><strong>熟悉素材：</strong>${entry.usesFamiliarMaterials ? "相关话题已命中" : "未见明显命中"}</span>
                <span><strong>记忆候选：</strong>${entry.canBecomeCandidate ? "适合家属复核" : "暂不建议沉淀"}</span>
            </div>
        </article>
    `).join("");
}


function getMemoryCandidateDraft(candidate) {
    return memoryCandidateDrafts.get(candidate.id) || {
        suggested_title: candidate.suggested_title || "",
        suggested_description: candidate.suggested_description || "",
        suggested_material_type: candidate.suggested_material_type || "old_event",
        related_person: candidate.related_person || "",
        sensitivity_level: candidate.sensitivity_level || "low",
    };
}


function updateMemoryCandidateDraft(candidateId, field, value) {
    const candidate = currentMemoryCandidates.find((item) => String(item.id) === String(candidateId));
    if (!candidate) {
        return;
    }
    const draft = { ...getMemoryCandidateDraft(candidate), [field]: value };
    memoryCandidateDrafts.set(candidate.id, draft);
}


function toggleMemoryCandidateEditor(candidateId) {
    openMemoryCandidateEditorId = String(openMemoryCandidateEditorId) === String(candidateId) ? null : candidateId;
    renderMemoryCandidates();
}


function markMemoryCandidateSensitive(candidateId) {
    const candidate = currentMemoryCandidates.find((item) => String(item.id) === String(candidateId));
    if (!candidate) {
        return;
    }
    memoryCandidateDrafts.set(candidate.id, {
        ...getMemoryCandidateDraft(candidate),
        suggested_material_type: "sensitive_memory",
        sensitivity_level: "high",
    });
    openMemoryCandidateEditorId = candidate.id;
    setChatHistoryStatus("已为这条候选预填“敏感记忆 + high”，请确认后再加入素材库。", "warning");
    renderMemoryCandidates();
}


function renderMemoryCandidateGroup(title, description, candidates, emptyText) {
    if (!candidates.length) {
        return `
            <section class="chat-history-candidate-group">
                <div class="chat-history-candidate-group-head">
                    <div>
                        <h3>${escapeHtml(title)}</h3>
                        <p>${escapeHtml(description)}</p>
                    </div>
                </div>
                <div class="log-empty">
                    <strong>${escapeHtml(emptyText)}</strong>
                </div>
            </section>
        `;
    }

    const isCollapsibleGroup = candidates.every((candidate) => candidate.status !== "pending");
    const wrapperTag = isCollapsibleGroup ? "details" : "section";
    const headTag = isCollapsibleGroup ? "summary" : "div";
    const wrapperAttrs = isCollapsibleGroup ? "" : "";
    return `
        <${wrapperTag} class="chat-history-candidate-group candidate-review-group" ${wrapperAttrs}>
            <${headTag} class="chat-history-candidate-group-head">
                <div>
                    <h3>${escapeHtml(title)}</h3>
                    <p>${escapeHtml(description)}</p>
                </div>
                <span class="status-pill">${escapeHtml(String(candidates.length))} 条</span>
            </${headTag}>
            <div class="chat-history-candidate-list">
                ${candidates.map((candidate) => {
                    const draft = getMemoryCandidateDraft(candidate);
                    const isEditorOpen = String(openMemoryCandidateEditorId) === String(candidate.id);
                    return `
                        <article class="chat-history-candidate-card ${candidate.is_sensitive ? "chat-history-candidate-sensitive" : ""} ${candidate.status || "pending"}">
                            <div class="chat-history-candidate-card-head">
                                <div class="history-tag-row">
                                    <span class="status-pill">${escapeHtml(materialTypeLabels[candidate.suggested_material_type] || candidate.suggested_material_type || "记忆候选")}</span>
                                    <span class="status-pill ${candidate.status === "approved" ? "success" : candidate.status === "rejected" ? "neutral" : "pending"}">${escapeHtml(candidate.status || "pending")}</span>
                                    ${candidate.is_sensitive ? '<span class="status-pill warning">敏感</span>' : '<span class="status-pill success">非敏感</span>'}
                                    ${candidate.dedup_warning ? `<span class="memory-warning-badge duplicate" title="${escapeHtml(candidate.dedup_warning)}">⚠️ 疑似重复</span>` : ""}
                                    ${candidate.conflict_warning ? `<span class="memory-warning-badge conflict" title="${escapeHtml(candidate.conflict_warning)}">❗ 内容冲突</span>` : ""}
                                </div>
                                ${candidate.status === "approved" ? '<span class="status-pill success">已加入熟悉素材库</span>' : ""}
                            </div>
                            <h4>${escapeHtml(candidate.suggested_title || "未命名候选")}</h4>
                            <div class="candidate-memory-text">
                                <span>提取的记忆文本</span>
                                <p>${escapeHtml(candidate.suggested_description || "暂无建议描述。")}</p>
                            </div>
                            <div class="candidate-source-summary">
                                <span>原对话摘要</span>
                                <p>${escapeHtml(candidate.source_message || "未记录")}</p>
                            </div>
                            <div class="chat-history-candidate-meta">
                                <span><strong>关联人物：</strong>${escapeHtml(candidate.related_person || "未填写")}</span>
                                <span><strong>建议类型：</strong>${escapeHtml(materialTypeLabels[candidate.suggested_material_type] || candidate.suggested_material_type || "旧事件")}</span>
                                <span><strong>敏感等级：</strong>${escapeHtml(candidate.sensitivity_level || "low")}</span>
                                <span><strong>来源时间：</strong>${escapeHtml(formatHistoryDateTime(candidate.created_at))}</span>
                                <span><strong>审核时间：</strong>${escapeHtml(candidate.reviewed_at ? formatHistoryDateTime(candidate.reviewed_at) : "待审核")}</span>
                            </div>
                            ${candidate.is_sensitive ? `
                                <div class="chat-history-candidate-warning">
                                    <strong>敏感内容必须由家属确认后才能进入长期素材库。</strong>
                                    <span>敏感素材不会主动刺激患者，只会在相关话题触发时配合安全模板使用。</span>
                                </div>
                            ` : ""}
                            ${candidate.status === "pending" ? `
                                <div class="chat-history-candidate-actions">
                                    <button type="button" class="ghost-button memory-reject-button swipe-reject-button" data-candidate-id="${candidate.id}">← 左滑拒绝</button>
                                    <button type="button" class="ghost-button memory-approve-button swipe-approve-button" data-candidate-id="${candidate.id}">右滑接受 →</button>
                                    <button type="button" class="ghost-button memory-sensitive-button" data-candidate-id="${candidate.id}">标记为敏感</button>
                                    <button type="button" class="ghost-button memory-edit-button" data-candidate-id="${candidate.id}">${isEditorOpen ? "收起编辑" : "编辑后加入"}</button>
                                </div>
                                ${isEditorOpen ? `
                                    <div class="chat-history-candidate-editor">
                                        <div class="materials-form-grid">
                                            <label class="field materials-span-two">
                                                <span>建议标题</span>
                                                <input type="text" class="candidate-draft-field" data-candidate-id="${candidate.id}" data-field="suggested_title" value="${escapeHtml(draft.suggested_title)}">
                                            </label>
                                            <label class="field materials-span-two">
                                                <span>建议描述</span>
                                                <textarea rows="3" class="candidate-draft-field" data-candidate-id="${candidate.id}" data-field="suggested_description">${escapeHtml(draft.suggested_description)}</textarea>
                                            </label>
                                            <label class="field">
                                                <span>建议类型</span>
                                                <select class="candidate-draft-field" data-candidate-id="${candidate.id}" data-field="suggested_material_type">
                                                    ${Object.entries(materialTypeLabels).map(([value, label]) => `
                                                        <option value="${escapeHtml(value)}" ${draft.suggested_material_type === value ? "selected" : ""}>${escapeHtml(label)}</option>
                                                    `).join("")}
                                                </select>
                                            </label>
                                            <label class="field">
                                                <span>关联人物</span>
                                                <input type="text" class="candidate-draft-field" data-candidate-id="${candidate.id}" data-field="related_person" value="${escapeHtml(draft.related_person)}">
                                            </label>
                                            <label class="field">
                                                <span>敏感等级</span>
                                                <select class="candidate-draft-field" data-candidate-id="${candidate.id}" data-field="sensitivity_level">
                                                    ${["low", "medium", "high"].map((value) => `
                                                        <option value="${escapeHtml(value)}" ${draft.sensitivity_level === value ? "selected" : ""}>${escapeHtml(value)}</option>
                                                    `).join("")}
                                                </select>
                                            </label>
                                        </div>
                                        <div class="chat-history-candidate-editor-actions">
                                            <button type="button" class="ghost-button memory-approve-draft-button" data-candidate-id="${candidate.id}">保存后加入素材库</button>
                                        </div>
                                    </div>
                                ` : ""}
                            ` : candidate.status === "approved" ? `
                                <div class="chat-history-candidate-actions">
                                    <a class="ghost-button" href="/materials">查看素材库</a>
                                </div>
                            ` : `
                                <div class="chat-history-candidate-warning">
                                    <strong>已忽略</strong>
                                    <span>这条候选不会进入长期素材库。</span>
                                </div>
                            `}
                        </article>
                    `;
                }).join("")}
            </div>
        </${wrapperTag}>
    `;
}


function renderMemoryCandidates() {
    const container = element("memory-candidate-list");
    if (!container) {
        return;
    }
    const pendingCandidates = currentMemoryCandidates.filter((candidate) => candidate.status === "pending");
    const approvedCandidates = currentMemoryCandidates.filter((candidate) => candidate.status === "approved");
    const rejectedCandidates = currentMemoryCandidates.filter((candidate) => candidate.status === "rejected");

    container.innerHTML = [
        renderMemoryCandidateGroup("待审核 pending", "需要家属确认后才能沉淀为长期熟悉素材。", pendingCandidates, "目前没有待审核候选。"),
        renderMemoryCandidateGroup("已加入素材库 approved", "已审核通过，并已同步进入熟悉素材库。", approvedCandidates, "目前还没有审核通过的候选。"),
        renderMemoryCandidateGroup("已忽略 rejected", "已明确不进入长期素材库。", rejectedCandidates, "目前还没有被忽略的候选。"),
    ].join("");

    container.querySelectorAll(".memory-approve-button").forEach((button) => {
        button.addEventListener("click", () => approveMemoryCandidate(button.dataset.candidateId));
    });
    container.querySelectorAll(".memory-approve-draft-button").forEach((button) => {
        button.addEventListener("click", () => approveMemoryCandidate(button.dataset.candidateId, { useDraft: true }));
    });
    container.querySelectorAll(".memory-reject-button").forEach((button) => {
        button.addEventListener("click", () => rejectMemoryCandidate(button.dataset.candidateId));
    });
    container.querySelectorAll(".memory-sensitive-button").forEach((button) => {
        button.addEventListener("click", () => markMemoryCandidateSensitive(button.dataset.candidateId));
    });
    container.querySelectorAll(".memory-edit-button").forEach((button) => {
        button.addEventListener("click", () => toggleMemoryCandidateEditor(button.dataset.candidateId));
    });
    container.querySelectorAll(".candidate-draft-field").forEach((field) => {
        field.addEventListener("input", () => updateMemoryCandidateDraft(field.dataset.candidateId, field.dataset.field, field.value));
        field.addEventListener("change", () => updateMemoryCandidateDraft(field.dataset.candidateId, field.dataset.field, field.value));
    });
}


function bindChatHistoryFilters() {
    ["chat-history-search", "chat-history-type-filter", "chat-history-date-filter", "chat-history-event-filter"].forEach((id) => {
        const node = element(id);
        if (!node || node.dataset.bound === "true") {
            return;
        }
        node.dataset.bound = "true";
        node.addEventListener("input", renderChatHistoryPage);
        node.addEventListener("change", renderChatHistoryPage);
    });
}


function renderChatHistoryPage() {
    bindChatHistoryFilters();
    const entries = buildChatHistoryEntries();
    renderChatHistoryOverview(entries);
    renderChatHistoryEntries(filterChatHistoryEntries(entries));
    renderMemoryCandidates();
}


async function approveMemoryCandidate(candidateId, options = {}) {
    if (!currentUserId || !candidateId) {
        return;
    }
    try {
        const buttonSelector = options.useDraft ? ".memory-approve-draft-button" : ".memory-approve-button";
        const button = document.querySelector(`${buttonSelector}[data-candidate-id="${candidateId}"]`);
        if (button) {
            button.disabled = true;
        }
        const candidate = currentMemoryCandidates.find((item) => String(item.id) === String(candidateId));
        const draft = options.useDraft && candidate ? getMemoryCandidateDraft(candidate) : null;
        const response = await fetch(`/api/memory-candidates/${encodeURIComponent(currentUserId)}/${encodeURIComponent(candidateId)}/approve`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(draft || {})
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "加入素材库失败");
        }
        currentMemoryCandidates = Array.isArray(data.candidates) ? [...data.candidates] : currentMemoryCandidates;
        currentFamiliarMaterials = Array.isArray(data.materials) ? [...data.materials] : currentFamiliarMaterials;
        currentFamiliarMaterialStatus = data.material_status ? { ...data.material_status } : currentFamiliarMaterialStatus;
        memoryCandidateDrafts.delete(Number(candidateId));
        openMemoryCandidateEditorId = null;
        setChatHistoryStatus("记忆候选已加入熟悉素材库。", "success");
        renderAll();
    } catch (error) {
        setChatHistoryStatus(error.message || "加入素材库失败，请稍后再试。", "warning");
        console.error(error);
    } finally {
        const buttonSelector = options.useDraft ? ".memory-approve-draft-button" : ".memory-approve-button";
        const button = document.querySelector(`${buttonSelector}[data-candidate-id="${candidateId}"]`);
        if (button) {
            button.disabled = false;
        }
    }
}


async function rejectMemoryCandidate(candidateId) {
    if (!currentUserId || !candidateId) {
        return;
    }
    try {
        const response = await fetch(`/api/memory-candidates/${encodeURIComponent(currentUserId)}/${encodeURIComponent(candidateId)}/reject`, {
            method: "POST"
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "忽略候选失败");
        }
        currentMemoryCandidates = Array.isArray(data.candidates) ? [...data.candidates] : currentMemoryCandidates;
        memoryCandidateDrafts.delete(Number(candidateId));
        openMemoryCandidateEditorId = null;
        setChatHistoryStatus("这条记忆候选已忽略。", "success");
        renderAll();
    } catch (error) {
        setChatHistoryStatus(error.message || "忽略候选失败，请稍后再试。", "warning");
        console.error(error);
    }
}


function metricRows(items) {
    return items.map(([label, value]) => `
        <div class="debug-metric-row">
            <span>${escapeHtml(label)}</span>
            <strong>${escapeHtml(value ?? "-")}</strong>
        </div>
    `).join("");
}


async function hydrateDebugDashboard() {
    try {
        const [statusResponse, lastChatResponse, testResultsResponse, summaryResponse, eventsResponse] = await Promise.all([
            fetch("/api/debug/llm-status"),
            fetch("/api/debug/last-chat"),
            fetch("/api/debug/test-results?include_markdown=false"),
            fetch(`/api/caregiver/${encodeURIComponent(currentCaregiverPatientId)}/summary`),
            fetch(`/api/caregiver/${encodeURIComponent(currentCaregiverPatientId)}/events`)
        ]);
        if (statusResponse.ok) {
            currentLlmStatus = await statusResponse.json();
        }
        if (lastChatResponse.ok) {
            const payload = await lastChatResponse.json();
            currentLastChatDiagnostics = payload.diagnostics || null;
        }
        if (testResultsResponse.ok) {
            currentTestResults = await testResultsResponse.json();
        }
        if (summaryResponse.ok) {
            currentCaregiverInsight = await summaryResponse.json();
        }
        if (eventsResponse.ok) {
            const payload = await eventsResponse.json();
            currentCaregiverEvents = Array.isArray(payload.events) ? payload.events : [];
        }
    } catch (error) {
        console.warn("[debug] dashboard hydrate failed", error);
    }
    renderDebugDashboard();
}


function renderDebugDashboard() {
    if (!isPage("debug_dashboard")) {
        return;
    }

    const status = currentLlmStatus || {};
    const providerAvailable = element("debug-provider-availability");
    if (providerAvailable) {
        providerAvailable.textContent = status.available ? "可用" : "未配置/不可用";
        providerAvailable.className = `status-pill ${status.available ? "success" : "warning"}`;
    }
    const llmGrid = element("debug-llm-status-grid");
    if (llmGrid) {
        llmGrid.innerHTML = metricRows([
            ["当前 provider", providerDisplayName(status.provider)],
            ["当前 model", status.model],
            ["base_url", status.base_url || "-"],
            ["API key", status.api_key_configured ? "已配置" : "未配置"],
            ["页面聊天默认", status.provider === "deepseek" ? "DeepSeek 主模型" : `${providerDisplayName(status.provider)}（请确认是否为调试配置）`],
            ["fallback", status.fallback_enabled ? "开启" : "关闭"],
            ["timeout", `${status.timeout_seconds ?? "-"} 秒`],
            ["max output chars", status.max_output_chars],
            ["状态原因", status.availability_reason],
        ]);
    }

    const deepseek = (currentTestResults && currentTestResults.deepseek_demo) || {};
    const deepseekFile = Array.isArray(currentTestResults?.files)
        ? currentTestResults.files.find((file) => file.filename === "deepseek_demo_patient_report.json")
        : null;
    const deepseekNode = element("debug-deepseek-test");
    if (deepseekNode) {
        if (!Object.keys(deepseek).length) {
            deepseekNode.innerHTML = `<div class="log-empty"><strong>尚未运行测试。</strong><span>请运行 python scripts/test_deepseek_demo_patient.py --provider deepseek</span></div>`;
        } else {
            deepseekNode.innerHTML = metricRows([
                ["结论", deepseek.verdict || "-"],
                ["平均质量分", deepseek.average_quality_score],
                ["Fallback 次数", deepseek.fallback_count],
                ["Postprocess 次数", deepseek.postprocess_count],
                ["高风险事件", deepseek.high_risk_event_count],
                ["中风险事件", deepseek.medium_risk_event_count],
                ["用药提醒事件", deepseek.medication_reminder_event_count],
                ["报告更新时间", deepseekFile?.modified_at || "-"],
                ["severe harmful reply 是否为 0", Number(deepseek.severe_harmful_reply_count || 0) === 0 ? "是（0）" : `否（${deepseek.severe_harmful_reply_count}）`],
                ["medication hallucination 是否为 0", Number(deepseek.medication_hallucination_count || 0) === 0 ? "是（0）" : `否（${deepseek.medication_hallucination_count}）`],
                ["deceased spouse direct correction 是否为 0", Number(deepseek.deceased_spouse_direct_correction_count || 0) === 0 ? "是（0）" : `否（${deepseek.deceased_spouse_direct_correction_count}）`],
                ["wandering unsafe encouragement 是否为 0", Number(deepseek.wandering_unsafe_encouragement_count || 0) === 0 ? "是（0）" : `否（${deepseek.wandering_unsafe_encouragement_count}）`],
            ]);
        }
    }

    const diag = currentLastChatDiagnostics || {};
    const lastChatNode = element("debug-last-chat-summary");
    if (lastChatNode) {
        lastChatNode.innerHTML = Object.keys(diag).length
            ? metricRows([
                ["实际使用", diag.template_used ? "Template fallback" : diag.fallback_used ? "Mock fallback" : providerDisplayName(diag.actual_provider || diag.provider)],
                ["User message", compactDebugText(diag.user_message, 120)],
                ["原始请求", `${providerDisplayName(diag.requested_provider || "-")} · ${diag.requested_model || diag.model || "-"}`],
                ["Provider", diag.actual_provider || diag.provider],
                ["Model", diag.model],
                ["base_url", diag.base_url || "-"],
                ["API key", diag.api_key_configured ? "已配置" : "未配置"],
                ["Fallback", yesNo(diag.fallback_used)],
                ["Fallback reason", diag.fallback_reason || "-"],
                ["Postprocess", yesNo(diag.postprocess_used)],
                ["Template", diag.template_used ? (diag.template_name || "template_fallback") : "-"],
                ["Guard reason", diag.guard_reason || "-"],
                ["Detected state", diag.detected_state || "-"],
                ["Strategy", diag.strategy || "-"],
                ["Response time", diag.response_time_ms ? `${diag.response_time_ms} ms` : "-"],
            ])
            : `<div class="log-empty"><strong>还没有聊天诊断。</strong><span>请打开 /conversation?debug=1 发送一句话。</span></div>`;
    }
    setTextIfPresent("debug-last-raw", compactDebugText(diag.raw_llm_reply));
    setTextIfPresent("debug-last-final", compactDebugText(diag.final_assistant_reply));

    const insight = currentCaregiverInsight || {};
    const riskNode = element("debug-caregiver-risk");
    if (riskNode) {
        const risk = insight.risk_level || "low";
        riskNode.textContent = `${severityLabels[risk] || risk}风险`;
        riskNode.className = `status-pill ${risk === "high" || risk === "medium" ? "warning" : "success"}`;
    }
    const unresolved = currentCaregiverEvents.filter((event) => !event.resolved).length;
    const unresolvedNode = element("debug-caregiver-unresolved-count");
    if (unresolvedNode) {
        unresolvedNode.textContent = `未处理 ${unresolved}`;
        unresolvedNode.className = `status-pill ${unresolved ? "warning" : "success"}`;
    }
    setTextIfPresent("debug-caregiver-summary", insight.today_summary || "暂无新的家属端摘要。");
    renderCaregiverEventDetails("debug-caregiver-events", currentCaregiverEvents.slice(0, 5));
}


async function hydrateTestResults() {
    try {
        const [testResultsResponse, statusResponse, lastChatResponse] = await Promise.all([
            fetch("/api/debug/test-results?include_markdown=true"),
            fetch("/api/debug/llm-status"),
            fetch("/api/debug/last-chat")
        ]);
        if (testResultsResponse.ok) {
            currentTestResults = await testResultsResponse.json();
        }
        if (statusResponse.ok) {
            currentLlmStatus = await statusResponse.json();
        }
        if (lastChatResponse.ok) {
            const payload = await lastChatResponse.json();
            currentLastChatDiagnostics = payload.diagnostics || null;
        }
    } catch (error) {
        console.warn("[debug] test results unavailable", error);
    }
    renderTestResults();
}


function verdictClass(verdict) {
    const normalized = String(verdict || "").toUpperCase();
    if (normalized === "PASS") {
        return "success";
    }
    if (normalized === "FAIL") {
        return "danger";
    }
    return "warning";
}


function formatScoreValue(value, suffix = "/10") {
    if (value === null || value === undefined || value === "") {
        return "-";
    }
    const numeric = Number(value);
    if (Number.isFinite(numeric)) {
        return `${numeric.toFixed(2)}${suffix}`;
    }
    return String(value);
}


function formatCountValue(value) {
    if (value === null || value === undefined || value === "") {
        return "-";
    }
    return String(value);
}


function setHtmlIfPresent(id, html) {
    const node = element(id);
    if (node) {
        node.innerHTML = html;
    }
}


function reportCommandText(filename) {
    if (String(filename || "").includes("controlled_llm_comparison_report")) {
        return "venv/bin/python scripts/evaluate_controlled_llm_comparison.py";
    }
    if (String(filename || "").includes("deepseek_demo_patient_report")) {
        return "venv/bin/python scripts/test_deepseek_demo_patient.py --provider deepseek";
    }
    return "";
}


function renderTestResults() {
    if (!isPage("test_results")) {
        return;
    }
    const files = Array.isArray(currentTestResults?.files) ? currentTestResults.files : [];
    const deepseekMetrics = currentTestResults?.deepseek_demo || {};
    const comparison = currentTestResults?.controlled_comparison || {};
    const comparisonMetrics = comparison.metrics || {};
    const acceptance = currentTestResults?.acceptance || {};
    const pageChat = currentTestResults?.page_chat || {};

    const deepseekMarkdown = files.find((file) => file.filename === "deepseek_demo_patient_report.md");
    const comparisonMarkdown = files.find((file) => file.filename === "controlled_llm_comparison_report.md");
    const diag = currentLastChatDiagnostics || null;
    const runtime = currentLlmStatus || {};
    const hasRecentPageChat = Boolean(diag && (diag.actual_provider || diag.provider));
    const pageChatPass = hasRecentPageChat
        && String(diag.actual_provider || diag.provider || "").toLowerCase() === "deepseek"
        && String(diag.model || "").toLowerCase() === "deepseek-v4-flash"
        && !diag.fallback_used;
    const overviewGrid = element("test-results-overview-grid");
    if (overviewGrid) {
        overviewGrid.innerHTML = `
            <article class="test-results-overview-card">
                <div class="test-results-overview-head">
                    <strong>DeepSeek 主聊天</strong>
                    <span class="status-pill ${hasRecentPageChat ? verdictClass(pageChatPass ? "PASS" : "NEEDS_REVIEW") : "warning"}">${hasRecentPageChat ? (pageChatPass ? "PASS" : "NEEDS_REVIEW") : "待验证"}</span>
                </div>
                ${hasRecentPageChat ? `
                    <div class="debug-metric-list">
                        ${metricRows([
                            ["actual_provider", diag.actual_provider || diag.provider || "-"],
                            ["model", diag.model || runtime.model || "-"],
                            ["fallback_used", String(Boolean(diag.fallback_used))],
                            ["状态", pageChatPass ? "PASS" : "NEEDS_REVIEW"],
                        ])}
                    </div>
                ` : `
                    <p>请运行 test_page_chat_deepseek.py</p>
                    <code class="test-results-inline-command">${escapeHtml(pageChat.command || "CHAT_URL=http://127.0.0.1:8001/chat venv/bin/python scripts/test_page_chat_deepseek.py")}</code>
                `}
            </article>
            <article class="test-results-overview-card">
                <div class="test-results-overview-head">
                    <strong>DeepSeek Demo Patient</strong>
                    <span class="status-pill ${verdictClass(deepseekMetrics.verdict)}">${escapeHtml(deepseekMetrics.verdict || "待生成")}</span>
                </div>
                ${Object.keys(deepseekMetrics).length ? `
                    <div class="debug-metric-list">
                        ${metricRows([
                            ["平均分", formatScoreValue(deepseekMetrics.average_quality_score)],
                            ["fallback_count", formatCountValue(deepseekMetrics.fallback_count)],
                            ["postprocess_count", formatCountValue(deepseekMetrics.postprocess_count)],
                            ["high_risk_event_count", formatCountValue(deepseekMetrics.high_risk_event_count)],
                            ["medium_risk_event_count", formatCountValue(deepseekMetrics.medium_risk_event_count)],
                        ])}
                    </div>
                ` : `
                    <p>尚未生成 DeepSeek Demo 报告</p>
                    <code class="test-results-inline-command">venv/bin/python scripts/test_deepseek_demo_patient.py --provider deepseek</code>
                `}
            </article>
            <article class="test-results-overview-card">
                <div class="test-results-overview-head">
                    <strong>Controlled Comparison</strong>
                    <span class="status-pill ${verdictClass(comparisonMetrics.verdict)}">${escapeHtml(comparisonMetrics.verdict || "待生成")}</span>
                </div>
                ${Object.keys(comparisonMetrics).length ? `
                    <div class="debug-metric-list">
                        ${metricRows([
                            ["baseline_direct_llm", formatScoreValue(comparisonMetrics.baseline_average_quality_score)],
                            ["care_system", formatScoreValue(comparisonMetrics.average_quality_score)],
                            ["improvement", comparisonMetrics.score_improvement !== null && comparisonMetrics.score_improvement !== undefined ? `${Number(comparisonMetrics.score_improvement) > 0 ? "+" : ""}${comparisonMetrics.score_improvement}` : "-"],
                            ["状态", comparisonMetrics.verdict || "-"],
                        ])}
                    </div>
                ` : `
                    <p>尚未生成 Controlled Comparison 报告</p>
                    <code class="test-results-inline-command">venv/bin/python scripts/evaluate_controlled_llm_comparison.py</code>
                `}
            </article>
            <article class="test-results-overview-card">
                <div class="test-results-overview-head">
                    <strong>v0.5 验收状态</strong>
                    <span class="status-pill ${acceptance.has_result ? "success" : "warning"}">${acceptance.has_result ? "已生成" : "待运行"}</span>
                </div>
                <p>${acceptance.has_result ? "已检测到独立验收结果文件。" : "当前没有独立验收结果文件。可直接运行一键验收命令。"}</p>
                <code class="test-results-inline-command">venv/bin/python scripts/run_v05_acceptance_check.py</code>
            </article>
        `;
    }

    const deepseekSummary = element("deepseek-demo-summary");
    if (deepseekSummary) {
        deepseekSummary.innerHTML = Object.keys(deepseekMetrics).length ? `
            <div class="test-results-summary-grid">
                <div class="test-results-summary-card">
                    <span>provider</span>
                    <strong>${escapeHtml(deepseekMetrics.provider || "deepseek")}</strong>
                </div>
                <div class="test-results-summary-card">
                    <span>model</span>
                    <strong>${escapeHtml(deepseekMetrics.model || "deepseek-v4-flash")}</strong>
                </div>
                <div class="test-results-summary-card">
                    <span>average_quality_score</span>
                    <strong>${escapeHtml(formatScoreValue(deepseekMetrics.average_quality_score))}</strong>
                </div>
                <div class="test-results-summary-card">
                    <span>final verdict</span>
                    <strong>${escapeHtml(deepseekMetrics.verdict || "-")}</strong>
                </div>
            </div>
        ` : `
            <div class="log-empty">
                <strong>尚未生成 DeepSeek Demo 报告</strong>
                <span>运行：venv/bin/python scripts/test_deepseek_demo_patient.py --provider deepseek</span>
            </div>
        `;
    }

    setHtmlIfPresent("deepseek-demo-metric-table", Object.keys(deepseekMetrics).length ? [
        ["provider", deepseekMetrics.provider || "deepseek"],
        ["model", deepseekMetrics.model || "deepseek-v4-flash"],
        ["average_quality_score", formatScoreValue(deepseekMetrics.average_quality_score)],
        ["fallback_count", formatCountValue(deepseekMetrics.fallback_count)],
        ["postprocess_count", formatCountValue(deepseekMetrics.postprocess_count)],
        ["high_risk_event_count", formatCountValue(deepseekMetrics.high_risk_event_count)],
        ["medium_risk_event_count", formatCountValue(deepseekMetrics.medium_risk_event_count)],
        ["medication_hallucination", formatCountValue(deepseekMetrics.medication_hallucination_count)],
        ["deceased_spouse_direct_correction", formatCountValue(deepseekMetrics.deceased_spouse_direct_correction_count)],
        ["wandering_unsafe_encouragement", formatCountValue(deepseekMetrics.wandering_unsafe_encouragement_count)],
        ["final verdict", deepseekMetrics.verdict || "-"],
    ].map(([label, value]) => `
        <tr>
            <th>${escapeHtml(label)}</th>
            <td>${escapeHtml(String(value ?? "-"))}</td>
        </tr>
    `).join("") : `
        <tr>
            <th>状态</th>
            <td>尚未生成报告</td>
        </tr>
    `);
    setTextIfPresent("deepseek-demo-markdown", deepseekMarkdown?.content || "尚未找到 Markdown 报告。");

    const comparisonSummaryNode = element("controlled-comparison-summary");
    if (comparisonSummaryNode) {
        comparisonSummaryNode.innerHTML = Object.keys(comparisonMetrics).length ? `
            <div class="test-results-summary-grid">
                <div class="test-results-summary-card">
                    <span>baseline_direct_llm</span>
                    <strong>${escapeHtml(formatScoreValue(comparisonMetrics.baseline_average_quality_score))}</strong>
                </div>
                <div class="test-results-summary-card">
                    <span>care_system</span>
                    <strong>${escapeHtml(formatScoreValue(comparisonMetrics.average_quality_score))}</strong>
                </div>
                <div class="test-results-summary-card">
                    <span>improvement</span>
                    <strong>${escapeHtml(comparisonMetrics.score_improvement !== null && comparisonMetrics.score_improvement !== undefined ? `${Number(comparisonMetrics.score_improvement) > 0 ? "+" : ""}${comparisonMetrics.score_improvement}` : "-")}</strong>
                </div>
                <div class="test-results-summary-card">
                    <span>verdict</span>
                    <strong>${escapeHtml(comparisonMetrics.verdict || "-")}</strong>
                </div>
                <div class="test-results-summary-card">
                    <span>场景数量</span>
                    <strong>${escapeHtml(String(comparison.scenario_count ?? 0))}</strong>
                </div>
            </div>
        ` : `
            <div class="log-empty">
                <strong>尚未生成 Controlled Comparison 报告</strong>
                <span>运行：venv/bin/python scripts/evaluate_controlled_llm_comparison.py</span>
            </div>
        `;
    }

    const topAdvantages = Array.isArray(comparison.top_advantages) ? comparison.top_advantages : [];
    setHtmlIfPresent("controlled-comparison-top-advantages", topAdvantages.length ? topAdvantages.map((item) => `
        <div class="test-results-advantage-card">
            <strong>${escapeHtml(item.scenario || "场景")}</strong>
            <span>提升 ${escapeHtml(item.improvement !== null && item.improvement !== undefined ? `${Number(item.improvement) > 0 ? "+" : ""}${item.improvement}` : "-")}</span>
            <p>${escapeHtml(item.key_difference || "完整照护链路整体更优。")}</p>
        </div>
    `).join("") : `<div class="analysis-empty-inline">暂时没有可显示的场景优势摘要。</div>`);

    const comparisonRows = Array.isArray(comparison.rows) ? comparison.rows : [];
    setHtmlIfPresent("controlled-comparison-rows", comparisonRows.length ? comparisonRows.map((row) => `
        <tr>
            <td>${escapeHtml(row.scenario || "-")}</td>
            <td>${escapeHtml(formatCountValue(row.baseline_score))}</td>
            <td>${escapeHtml(formatCountValue(row.care_system_score))}</td>
            <td>${escapeHtml(row.improvement !== null && row.improvement !== undefined ? `${Number(row.improvement) > 0 ? "+" : ""}${row.improvement}` : "-")}</td>
            <td>${escapeHtml(shortText(row.key_difference || "照护系统整体更优。", 80))}</td>
        </tr>
    `).join("") : `
        <tr>
            <td colspan="5">未读取到场景明细，仅显示总分。</td>
        </tr>
    `);
    setTextIfPresent("controlled-comparison-markdown", comparisonMarkdown?.content || "尚未找到 Markdown 报告。");

    const acceptanceSummary = element("acceptance-summary");
    if (acceptanceSummary) {
        acceptanceSummary.innerHTML = `
            <div class="test-results-summary-card test-results-summary-card-wide">
                <span>验收结果文件</span>
                <strong>${acceptance.has_result ? "已检测到结果文件" : "当前没有独立结果文件"}</strong>
                <p>${acceptance.has_result ? "可以直接查看输出结果。" : "当前页面显示命令与检查范围；运行脚本后请结合终端输出和本页报告一起展示。"}</p>
            </div>
        `;
    }
    const acceptanceChecks = Array.isArray(acceptance.checks) ? acceptance.checks : [];
    setHtmlIfPresent("acceptance-check-list", acceptanceChecks.map((item) => `
        <span class="app-inline-pill">${escapeHtml(item)}</span>
    `).join(""));

    const fileTable = element("test-results-file-table");
    if (fileTable) {
        if (!files.length) {
            fileTable.innerHTML = `
                <tr>
                    <td colspan="6">没有检测到报告配置，请先运行测试脚本。</td>
                </tr>
            `;
        } else {
            fileTable.innerHTML = files.map((file) => `
                <tr>
                    <td>${escapeHtml(file.filename || "-")}</td>
                    <td><span class="status-pill ${file.exists ? "success" : "warning"}">${file.exists ? "已生成" : "未生成"}</span></td>
                    <td>${escapeHtml(file.modified_at || "-")}</td>
                    <td>${escapeHtml(file.size_text || "-")}</td>
                    <td>${escapeHtml(file.description || "-")}${!file.exists && reportCommandText(file.filename) ? `<div class="test-results-file-hint">运行：${escapeHtml(reportCommandText(file.filename))}</div>` : ""}</td>
                    <td>${file.exists && file.content ? `<button type="button" class="ghost-button test-result-preview-button" data-filename="${escapeHtml(file.filename)}">查看</button>` : `<span class="test-results-missing-action">-</span>`}</td>
                </tr>
            `).join("");
        }
        fileTable.querySelectorAll(".test-result-preview-button").forEach((button) => {
            button.addEventListener("click", () => {
                const filename = button.dataset.filename || "";
                const target = files.find((file) => file.filename === filename);
                setTextIfPresent("test-results-preview", target?.content || "暂无内容。");
                const details = element("test-results-preview")?.closest("details");
                if (details) {
                    details.open = true;
                }
            });
        });
    }
}


function renderCaregiverLinks(targetId, caregivers) {
    const container = element(targetId);
    if (!container) {
        return;
    }

    if (!Array.isArray(caregivers) || !caregivers.length) {
        container.innerHTML = `
            <div class="log-empty">
                <strong>还没有添加协同成员。</strong>
                <span>可以先记录主要家属或照护人，后续用于提醒设置和异常同步。</span>
            </div>
        `;
        return;
    }

    container.innerHTML = caregivers.map((caregiver) => `
        <article class="care-record-card">
            <div>
                <strong>${escapeHtml(caregiver.caregiver_name || "家属")}${caregiver.is_primary ? " · 主要联系人" : ""}</strong>
                <span>${escapeHtml(caregiver.caregiver_role || "family")}</span>
                <span>${escapeHtml(caregiver.contact_info || "未填写联系方式")}</span>
            </div>
        </article>
    `).join("");
}


function updateProfileStatus(text, kind = "success") {
    const status = element("profile-status");
    if (!status) {
        return;
    }

    status.textContent = text;
    status.className = "status-pill";

    if (kind) {
        status.classList.add(kind);
    }
}


function updateComposerNote(text, kind = "") {
    const note = element("composer-help-text");
    if (note) {
        note.textContent = text;
        note.dataset.kind = kind;
    }
}


function collectProfilePayload() {
    if (!hasProfileForm()) {
        return {
            ...currentProfile,
            support_mode: getCurrentMode()
        };
    }

    return getCurrentProfileSnapshot();
}


async function saveProfile(options = {}) {
    if (!hasProfileForm()) {
        return currentProfile;
    }

    const payload = collectProfilePayload();
    const silent = Boolean(options.silent);
    const saveButton = element("save-button");

    if (!payload.name) {
        if (!silent) {
            updateProfileStatus("请先填写常用称呼，再保存档案。", "warning");
            element("name").focus();
        }
        return null;
    }

    try {
        if (!silent && saveButton) {
            saveButton.disabled = true;
            saveButton.textContent = "保存中…";
        }

        const response = await fetch("/save_profile", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok || data.status !== "ok") {
            throw new Error(data.detail || "保存失败");
        }

        currentProfile = { ...(data.profile || currentProfile) };
        currentUserId = currentProfile.id || currentUserId;
        fillProfileForm(currentProfile);
        renderAll();

        if (!silent) {
            updateProfileStatus("档案已保存。");
        }

        return currentProfile;
    } catch (error) {
        if (!silent) {
            updateProfileStatus("档案暂时未保存成功，请稍后再试。", "warning");
        }
        console.error(error);
        return null;
    } finally {
        if (!silent && saveButton) {
            saveButton.disabled = false;
            saveButton.textContent = saveButtonDefaultText;
        }
    }
}


async function sendMessage(options = {}) {
    const input = element("input");
    const sendButton = element("send-button");

    if (!input || !sendButton) {
        return;
    }
    if (sendButton.disabled) return { success: false, busy: true };

    const overrideMessage = typeof options.message === "string" ? options.message.trim() : "";
    const message = overrideMessage || input.value.trim();

    if (!message) {
        updateComposerNote("想好一句再说。", "warning");
        input.focus();
        return;
    }

    appendMessage("user", message);
    if (!overrideMessage) {
        input.value = "";
    } else {
        input.value = "";
        input.dispatchEvent(new Event("input", { bubbles: true }));
    }
    updateComposerNote("我在听。");
    window.ConversationVoice?.onThinking({
        source: options.source || "text"
    });
    sendButton.disabled = true;
    input.disabled = true;
    sendButton.textContent = "发送中...";
    if (typeof options.onBeforeRequest === "function") {
        options.onBeforeRequest({ message, source: options.source || "text" });
    }

    const previousLogs = [...currentLogs];
    currentLogs = [
        ...currentLogs,
        {
            role: "user",
            message,
            mode: getCurrentMode(),
            timestamp: formatLocalTimestamp(),
            repeated_flag: false,
            keyword_tags: ""
        }
    ].slice(-10);
    renderAll();
    const requestStartedAt = window.performance?.now?.() || Date.now();
    const controller = new AbortController();
    const requestTimeout = window.setTimeout(() => controller.abort(), 60000);

    try {
        const response = await fetch("/chat", {
            signal: controller.signal,
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                user_id: legacyProfileUserId() ? Number(legacyProfileUserId()) : null,
                message,
                mode: getCurrentMode(),
                patient_id: currentCaregiverPatientId,
                session_id: currentChatSessionId
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "聊天请求失败");
        }
        if (data.session_id) {
            currentChatSessionId = data.session_id;
            sessionStorage.setItem(chatSessionStorageKey, currentChatSessionId);
        }

        currentProfile = { ...(data.profile || currentProfile) };
        currentUserId = currentProfile.id || currentUserId;
        fillProfileForm(currentProfile);
        currentLogs = Array.isArray(data.logs)
            ? [...previousLogs, ...data.logs].slice(-10)
            : [
                ...currentLogs,
                {
                    role: "assistant",
                    message: data.reply,
                    mode: getCurrentMode(),
                    timestamp: formatLocalTimestamp(),
                    repeated_flag: false,
                    keyword_tags: ""
                }
            ].slice(-10);
        currentMemoryDigest = data.memory_digest ? { ...data.memory_digest } : buildMemoryDigest(currentProfile, currentLogs);
        currentLastChatDiagnostics = data.diagnostics || data.debug || null;
        renderConversationModelStatus(currentLastChatDiagnostics, currentLlmStatus);

        renderAll();
        updateComposerNote("继续说就好。");
        const chatLatencyMs = Math.max(0, Math.round((window.performance?.now?.() || Date.now()) - requestStartedAt));
        const result = {
            success: true,
            reply: data.reply,
            latency_ms: chatLatencyMs,
            diagnostics: data.diagnostics || data.debug || null,
            data
        };
        if (typeof options.onSuccess === "function") {
            options.onSuccess(result);
        }
        window.ConversationVoice?.handleAssistantReply(data.reply, {
            source: options.source || "text",
            chatLatencyMs,
            diagnostics: data.diagnostics || data.debug || null
        });
        return result;
    } catch (error) {
        currentLogs = previousLogs;
        input.value = message;
        renderAll();
        updateComposerNote("暂未收到回复，内容已保留。上一次请求可能已保存，请勿连续重试。", "warning");
        const chatLatencyMs = Math.max(0, Math.round((window.performance?.now?.() || Date.now()) - requestStartedAt));
        const failure = {
            success: false,
            latency_ms: chatLatencyMs,
            error_message: error instanceof Error ? error.message : "聊天请求失败"
        };
        if (typeof options.onError === "function") {
            options.onError(failure);
        }
        window.ConversationVoice?.onError({
            source: options.source || "text",
            chatLatencyMs,
            error: failure.error_message
        });
        console.error(error);
        return failure;
    } finally {
        window.clearTimeout(requestTimeout);
        sendButton.disabled = false;
        input.disabled = false;
        sendButton.textContent = sendButtonDefaultText;
        if (options.source !== "voice") input.focus();
    }
}


function getDeviceSettings() {
    try {
        const stored = localStorage.getItem(deviceToggleStorageKey);
        if (!stored) {
            return {
                meal: false,
                water: false,
                medicine: false,
                rest: false,
                autoplay: false,
                speechLength: "standard",
                speechRhythm: "steady"
            };
        }
        return {
            meal: false,
            water: false,
            medicine: false,
            rest: false,
            autoplay: false,
            speechLength: "standard",
            speechRhythm: "steady",
            ...JSON.parse(stored)
        };
    } catch (error) {
        console.error(error);
        return {
            meal: false,
            water: false,
            medicine: false,
            rest: false,
            autoplay: false,
            speechLength: "standard",
            speechRhythm: "steady"
        };
    }
}


function saveDeviceSettings(settings) {
    localStorage.setItem(deviceToggleStorageKey, JSON.stringify(settings));
}


function updateDeviceToggleUI(id, enabled) {
    const button = element(id);
    if (!button) {
        return;
    }

    button.dataset.enabled = enabled ? "true" : "false";
    button.setAttribute("aria-pressed", enabled ? "true" : "false");
    button.textContent = enabled ? "开启" : "关闭";
}


function updateDeviceSettingsStatus() {
    const settings = getDeviceSettings();
    const enabledReminders = currentReminders.filter((reminder) => reminder.is_enabled);
    const enabledKeys = Object.entries(settings)
        .filter(([key, enabled]) => ["autoplay"].includes(key) && Boolean(enabled))
        .map(([key]) => key);
    const status = element("device-settings-status");
    const summary = element("reminder-enabled-list");
    const voiceSummary = element("voice-settings-summary");

    const labelMap = {
        meal: "吃饭提醒",
        water: "喝水提醒",
        medicine: "吃药提醒",
        rest: "休息提醒",
        autoplay: "自动播报"
    };

    if (status) {
        status.textContent = enabledReminders.length
            ? `已启用 ${enabledReminders.length} 条提醒`
            : "当前未启用提醒";
    }

    if (summary) {
        summary.textContent = buildCareReminderSummary(currentReminders);
    }

    if (voiceSummary) {
        const speechLengthMap = {
            short: "简短播报",
            standard: "标准播报",
            long: "完整播报"
        };
        const speechRhythmMap = {
            gentle: "慢一些",
            steady: "标准节奏",
            calm: "更从容"
        };
        voiceSummary.textContent = `当前语音设置为${speechLengthMap[settings.speechLength] || "标准播报"}、${speechRhythmMap[settings.speechRhythm] || "标准节奏"}。`;
    }
}


function bindDeviceToggle(id, key) {
    const button = element(id);
    if (!button) {
        return;
    }

    button.addEventListener("click", () => {
        const settings = getDeviceSettings();
        settings[key] = !settings[key];
        saveDeviceSettings(settings);
        renderDeviceSettings();
    });
}


function bindDeviceSelect(id, key) {
    const input = element(id);
    if (!input) {
        return;
    }

    input.addEventListener("change", () => {
        const settings = getDeviceSettings();
        settings[key] = input.value;
        saveDeviceSettings(settings);
        renderDeviceSettings();
    });
}


function bindReminderCenter() {
    const saveButton = element("save-reminder-button");
    if (!saveButton) {
        return;
    }

    saveButton.addEventListener("click", saveReminder);
}


function bindEventLogForm() {
    const saveButton = element("save-event-button");
    if (!saveButton) {
        return;
    }

    saveButton.addEventListener("click", () => {
        const eventType = element("event-type")?.value || "other";
        const severity = element("event-severity")?.value || "low";
        const description = element("event-description")?.value.trim() || "";
        const createdBy = element("event-created-by")?.value.trim() || "family";

        createEventLog({
            event_type: eventType,
            severity,
            description,
            source: "care_log",
            created_by: createdBy
        });

        ["event-description", "event-created-by"].forEach((id) => {
            const node = element(id);
            if (node) {
                node.value = "";
            }
        });
    });
}


function bindCaregiverForm() {
    const saveButton = element("save-caregiver-button");
    if (!saveButton) {
        return;
    }

    saveButton.addEventListener("click", saveCaregiverLink);
}


async function saveCaregiverLink() {
    const saveButton = element("save-caregiver-button");
    const nameInput = element("caregiver-name");
    const roleInput = element("caregiver-role");
    const contactInput = element("caregiver-contact");
    const primaryInput = element("caregiver-primary");
    const payload = {
        user_profile_id: currentUserId,
        caregiver_name: nameInput?.value.trim() || "家属",
        caregiver_role: roleInput?.value.trim() || "family",
        contact_info: contactInput?.value.trim() || "",
        is_primary: Boolean(primaryInput?.checked)
    };

    try {
        if (saveButton) {
            saveButton.disabled = true;
            saveButton.textContent = "添加中";
        }
        const response = await fetch("/caregivers", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (!response.ok || data.status !== "ok") {
            throw new Error(data.detail || "成员添加失败");
        }
        currentCaregiverLinks = Array.isArray(data.caregiver_links) ? [...data.caregiver_links] : currentCaregiverLinks;
        [nameInput, roleInput, contactInput].forEach((node) => {
            if (node) {
                node.value = "";
            }
        });
        if (primaryInput) {
            primaryInput.checked = false;
        }
        renderAll();
    } catch (error) {
        console.error(error);
    } finally {
        if (saveButton) {
            saveButton.disabled = false;
            saveButton.textContent = "添加成员";
        }
    }
}


function getReminderPayload() {
    const typeInput = element("reminder-type");
    const titleInput = element("reminder-title");
    const timeInput = element("reminder-time");
    const repeatInput = element("reminder-repeat");
    const createdByInput = element("reminder-created-by");

    const reminderType = typeInput?.value || "medicine";
    return {
        id: editingReminderId,
        user_profile_id: currentUserId,
        reminder_type: reminderType,
        title: titleInput?.value.trim() || reminderTypeLabels[reminderType] || "照护提醒",
        scheduled_time: timeInput?.value || "",
        repeat_rule: repeatInput?.value || "daily",
        is_enabled: true,
        created_by: createdByInput?.value.trim() || "family"
    };
}


async function saveReminder() {
    const saveButton = element("save-reminder-button");
    const payload = getReminderPayload();

    try {
        if (saveButton) {
            saveButton.disabled = true;
            saveButton.textContent = "保存中";
        }

        const response = await fetch("/reminders", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (!response.ok || data.status !== "ok") {
            throw new Error(data.detail || "提醒保存失败");
        }

        currentReminders = Array.isArray(data.reminders) ? [...data.reminders] : currentReminders;
        editingReminderId = null;
        ["reminder-title", "reminder-time", "reminder-created-by"].forEach((id) => {
            const node = element(id);
            if (node) {
                node.value = "";
            }
        });
        renderAll();
    } catch (error) {
        console.error(error);
        setTextIfPresent("reminder-enabled-list", "提醒暂时没有保存成功，请稍后再试。");
    } finally {
        if (saveButton) {
            saveButton.disabled = false;
            saveButton.textContent = "添加提醒";
        }
    }
}


function editReminder(reminderId) {
    const reminder = currentReminders.find((item) => Number(item.id) === Number(reminderId));
    if (!reminder) {
        return;
    }

    editingReminderId = reminder.id;
    const typeInput = element("reminder-type");
    const titleInput = element("reminder-title");
    const timeInput = element("reminder-time");
    const repeatInput = element("reminder-repeat");
    const createdByInput = element("reminder-created-by");
    const saveButton = element("save-reminder-button");

    if (typeInput) {
        typeInput.value = reminder.reminder_type || "medicine";
    }
    if (titleInput) {
        titleInput.value = reminder.title || "";
    }
    if (timeInput) {
        timeInput.value = reminder.scheduled_time || "";
    }
    if (repeatInput) {
        repeatInput.value = reminder.repeat_rule || "daily";
    }
    if (createdByInput) {
        createdByInput.value = reminder.created_by || "";
    }
    if (saveButton) {
        saveButton.textContent = "保存修改";
    }
}


async function toggleReminder(reminderId, enabled) {
    if (!reminderId) {
        return;
    }

    try {
        const response = await fetch(`/reminders/${reminderId}`, {
            method: "PATCH",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                user_profile_id: currentUserId,
                is_enabled: enabled
            })
        });
        const data = await response.json();
        if (!response.ok || data.status !== "ok") {
            throw new Error(data.detail || "提醒状态更新失败");
        }
        currentReminders = Array.isArray(data.reminders) ? [...data.reminders] : currentReminders;
        renderAll();
    } catch (error) {
        console.error(error);
    }
}


async function updateReminderTaskStatus(reminderId, action, sourceButton = null) {
    if (!reminderId || !currentUserId) {
        return;
    }
    const actionMap = {
        confirm: {
            url: `/api/reminders/${encodeURIComponent(currentUserId)}/${encodeURIComponent(reminderId)}/confirm`,
            options: {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ confirmed_by: "caregiver" })
            }
        },
        miss: {
            url: `/api/reminders/${encodeURIComponent(currentUserId)}/${encodeURIComponent(reminderId)}/miss`,
            options: { method: "POST" }
        },
        skip: {
            url: `/api/reminders/${encodeURIComponent(currentUserId)}/${encodeURIComponent(reminderId)}/skip`,
            options: { method: "POST" }
        }
    };
    const target = actionMap[action];
    if (!target) {
        return;
    }
    const statusNode = element("analysis-reminder-action-status");
    const originalText = sourceButton ? sourceButton.textContent : "";
    const siblingButtons = sourceButton
        ? Array.from(sourceButton.closest(".analysis-task-actions")?.querySelectorAll("button") || [])
        : [];
    try {
        siblingButtons.forEach((button) => {
            button.disabled = true;
        });
        if (sourceButton) {
            sourceButton.textContent = "处理中";
        }
        if (statusNode) {
            statusNode.textContent = "正在更新提醒状态...";
            statusNode.dataset.kind = "pending";
        }
        const response = await fetch(target.url, target.options);
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "提醒状态更新失败");
        }
        currentReminders = Array.isArray(data.reminders) ? [...data.reminders] : currentReminders;
        await loadCareData();
        if (statusNode) {
            statusNode.textContent = "提醒状态已更新。";
            statusNode.dataset.kind = "success";
        }
    } catch (error) {
        if (statusNode) {
            statusNode.textContent = "提醒状态暂时没有更新成功，请稍后再试。";
            statusNode.dataset.kind = "warning";
        }
        console.error(error);
    } finally {
        siblingButtons.forEach((button) => {
            button.disabled = false;
        });
        if (sourceButton && originalText) {
            sourceButton.textContent = originalText;
        }
    }
}


async function resolveCaregiverEvent(eventId, sourceButton = null) {
    if (!eventId) {
        return;
    }
    const statusNode = element("caregiver-event-action-status");
    try {
        if (sourceButton) {
            sourceButton.disabled = true;
            sourceButton.textContent = "处理中";
        }
        if (statusNode) {
            statusNode.textContent = "正在标记风险事件...";
            statusNode.dataset.kind = "pending";
        }
        const response = await fetch(
            `/api/caregiver/${encodeURIComponent(currentCaregiverPatientId)}/events/${encodeURIComponent(eventId)}/resolve`,
            { method: "POST" }
        );
        const data = await response.json();
        if (!response.ok || data.status !== "ok") {
            throw new Error(data.detail || "事件处理失败");
        }
        await loadCareData();
        if (statusNode) {
            statusNode.textContent = "风险事件已标记处理。";
            statusNode.dataset.kind = "success";
        }
    } catch (error) {
        if (sourceButton) {
            sourceButton.disabled = false;
            sourceButton.textContent = "标记已处理";
        }
        if (statusNode) {
            statusNode.textContent = "风险事件暂时没有更新成功，请稍后再试。";
            statusNode.dataset.kind = "warning";
        }
        console.error(error);
    }
}


async function createEventLog(payload) {
    try {
        const response = await fetch("/event_logs", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                user_profile_id: currentUserId,
                ...payload
            })
        });
        const data = await response.json();
        if (!response.ok || data.status !== "ok") {
            throw new Error(data.detail || "事件记录失败");
        }
        currentEventLogs = Array.isArray(data.event_logs) ? [...data.event_logs] : currentEventLogs;
        renderAll();
    } catch (error) {
        console.error(error);
    }
}


function renderDeviceSettings() {
    const settings = getDeviceSettings();
    updateDeviceToggleUI("meal-toggle", settings.meal);
    updateDeviceToggleUI("water-toggle", settings.water);
    updateDeviceToggleUI("medicine-toggle", settings.medicine);
    updateDeviceToggleUI("rest-toggle", settings.rest);
    updateDeviceToggleUI("autoplay-toggle", settings.autoplay);

    const speechLengthSelect = element("speech-length-select");
    const speechRhythmSelect = element("speech-rhythm-select");
    if (speechLengthSelect) {
        speechLengthSelect.value = settings.speechLength || "standard";
    }
    if (speechRhythmSelect) {
        speechRhythmSelect.value = settings.speechRhythm || "steady";
    }
    updateDeviceSettingsStatus();
    renderReminderList("reminder-list", currentReminders);
}


function escapeHtml(text) {
    return String(text ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll("\"", "&quot;")
        .replaceAll("'", "&#39;");
}


window.sendMessage = sendMessage;
window.sendMessageFromVoice = function sendMessageFromVoice(transcript, options = {}) {
    return sendMessage({ ...options, message: transcript, source: "voice" });
};
window.saveProfile = saveProfile;

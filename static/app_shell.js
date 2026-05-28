const appBootstrap = window.APP_BOOTSTRAP || {};
const appRole = appBootstrap.appRole || document.body?.dataset.role || "patient";

document.addEventListener("DOMContentLoaded", async () => {
    if ((document.body?.dataset.page || "") !== "app_home") {
        return;
    }

    updatePatientClock();
    window.setInterval(updatePatientClock, 60 * 1000);

    try {
        const response = await fetch(`/app-summary?role=${encodeURIComponent(appRole)}`, {
            headers: { Accept: "application/json" }
        });
        if (!response.ok) {
            throw new Error(`summary request failed: ${response.status}`);
        }

        const payload = await response.json();
        const summary = payload.summary || {};
        if (payload.role === "caregiver") {
            renderCaregiverSummary(summary);
        } else {
            renderPatientSummary(summary);
        }
    } catch (error) {
        if (appRole === "caregiver") {
            renderCaregiverEmptyState();
        } else {
            renderPatientEmptyState();
        }
        console.warn("[app-shell] summary fallback", error);
    }
});


function appElement(id) {
    return document.getElementById(id);
}


function setText(id, value) {
    const target = appElement(id);
    if (!target) {
        return;
    }
    target.textContent = String(value ?? "");
}


function updatePatientClock() {
    const now = new Date();
    const hh = String(now.getHours()).padStart(2, "0");
    const mm = String(now.getMinutes()).padStart(2, "0");
    setText("patient-time-text", `${hh}:${mm}`);
}


function renderPatientSummary(summary) {
    const status = summary.current_status || {};
    const nextReminder = summary.next_reminder || null;
    const recentChat = summary.recent_chat || {};
    const safety = summary.safety_status || {};

    setText("patient-current-status", status.label || "陪伴中");
    setText(
        "patient-status-copy",
        status.voice_ready
            ? "如果想找家人、想确认安排，或者只是想慢慢说一句话，都可以从这里开始。"
            : "语音还没有配置好，先继续轻轻地打字聊天也可以。"
    );
    setText("patient-voice-status", status.voice_status || "语音状态暂时不可用");
    if (status.current_time) {
        setText("patient-time-text", status.current_time);
    }

    if (nextReminder) {
        setText("patient-next-reminder-title", `${nextReminder.type_label} · ${nextReminder.time}`);
        setText("patient-next-reminder-meta", nextReminder.title || "下一条提醒已经准备好。");
    } else {
        setText("patient-next-reminder-title", "今天还没有新的提醒");
        setText("patient-next-reminder-meta", "如果后面有新的安排，会安静地显示在这里。");
    }

    setText(
        "patient-recent-chat-role",
        recentChat.has_data
            ? recentChat.role === "assistant"
                ? "我刚才说过"
                : "你刚才说过"
            : "还没有新的对话"
    );
    setText(
        "patient-recent-chat-message",
        recentChat.message || "我们可以从一句轻轻的问候开始。"
    );

    setText("patient-safety-label", safety.label || "未开启定位");
    setText(
        "patient-safety-copy",
        safety.summary || "定位安全还没有启用，后续接入设备后会显示最近上报和安全区域状态。"
    );
}


function renderPatientEmptyState() {
    setText("patient-current-status", "陪伴中");
    setText("patient-status-copy", "首页数据稍后会回来，现在先保持安静陪伴也可以。");
    setText("patient-next-reminder-title", "暂时还没有新的提醒");
    setText("patient-next-reminder-meta", "如果后面有新的安排，会安静地显示在这里。");
    setText("patient-recent-chat-role", "还没有新的对话");
    setText("patient-recent-chat-message", "我们可以从一句轻轻的问候开始。");
    setText("patient-safety-label", "未开启定位");
    setText("patient-safety-copy", "安全状态暂时还没有新的数据。");
    setText("patient-voice-status", "语音状态稍后更新");
}


function renderCaregiverSummary(summary) {
    const reminderSummary = summary.reminder_summary || {};
    const recentEvents = Array.isArray(summary.recent_events) ? summary.recent_events : [];
    const memorySummary = summary.memory_summary || {};
    const safetySummary = summary.safety_summary || {};
    const nextReminder = reminderSummary.next_reminder || null;

    setText("caregiver-reminder-total", reminderSummary.total_count ?? 0);
    setText(
        "caregiver-reminder-status",
        `待处理 ${reminderSummary.pending_count ?? 0} · 关闭 ${reminderSummary.closed_count ?? 0}`
    );
    setText("caregiver-event-total", recentEvents.length);
    setText("caregiver-event-status", recentEvents.length ? "近期异常记录" : "近期无异常记录");
    setText("caregiver-chat-total", (memorySummary.follow_up_topics || []).length);
    setText(
        "caregiver-chat-status",
        memorySummary.last_updated_at ? `更新于 ${memorySummary.last_updated_at}` : "最近对话摘要"
    );

    setText(
        "caregiver-memory-summary",
        memorySummary.summary || "当前还没有足够的摘要，建议先从患者对话和家属档案开始累积。"
    );
    setText(
        "caregiver-memory-people",
        (memorySummary.mentioned_people || []).length
            ? `常提到：${memorySummary.mentioned_people.join("、")}`
            : "最近常提到的人还在积累"
    );
    setText(
        "caregiver-memory-topics",
        (memorySummary.follow_up_topics || []).length
            ? `常聊主题：${memorySummary.follow_up_topics.join("、")}`
            : "最近常聊的话题会显示在这里。"
    );
    setText(
        "caregiver-memory-updated",
        memorySummary.last_updated_at
            ? `最近更新时间：${memorySummary.last_updated_at}`
            : "最近更新时间：暂无"
    );

    if (nextReminder) {
        setText("caregiver-next-reminder-title", `${nextReminder.type_label} · ${nextReminder.time}`);
        setText(
            "caregiver-next-reminder-copy",
            `${nextReminder.title || "下一条提醒"} · 待处理 ${reminderSummary.pending_count ?? 0} 项`
        );
    } else {
        setText("caregiver-next-reminder-title", "今天还没有新的提醒");
        setText("caregiver-next-reminder-copy", "如果稍后新增提醒，这里会显示下一条安排。");
    }

    if (recentEvents.length) {
        const latestEvent = recentEvents[0];
        setText("caregiver-recent-event-title", latestEvent.event_type_label || "已记录事件");
        setText("caregiver-recent-event-copy", latestEvent.description || "最近的异常事件会显示在这里。");
    } else {
        setText("caregiver-recent-event-title", "暂无异常事件");
        setText("caregiver-recent-event-copy", "后续记录的情绪、拒药、离家倾向等事件会集中展示。");
    }

    renderEventList(recentEvents);

    setText(
        "caregiver-safety-title",
        safetySummary.safe_zone_status || "未开启定位"
    );
    setText(
        "caregiver-safety-copy",
        safetySummary.summary || "定位安全状态会在这里显示。"
    );
}


function renderCaregiverEmptyState() {
    setText("caregiver-reminder-status", "首页数据暂时不可用");
    setText("caregiver-event-status", "异常事件稍后更新");
    setText("caregiver-chat-status", "最近对话摘要稍后更新");
    setText("caregiver-memory-summary", "摘要暂时不可用，稍后会重新加载。");
    setText("caregiver-memory-people", "最近常提到的人还在积累");
    setText("caregiver-memory-topics", "最近常聊的话题会显示在这里。");
    setText("caregiver-memory-updated", "最近更新时间：暂无");
    setText("caregiver-next-reminder-title", "今天还没有新的提醒");
    setText("caregiver-next-reminder-copy", "如果稍后新增提醒，这里会显示下一条安排。");
    setText("caregiver-recent-event-title", "暂无异常事件");
    setText("caregiver-recent-event-copy", "后续记录的异常事件会集中展示。");
    setText("caregiver-safety-title", "未开启定位");
    setText("caregiver-safety-copy", "定位安全状态暂时还没有新的数据。");
    renderEventList([]);
}


function renderEventList(events) {
    const container = appElement("caregiver-recent-event-list");
    if (!container) {
        return;
    }

    if (!events.length) {
        container.innerHTML = '<span class="app-inline-list-empty">最近没有新的异常事件。</span>';
        return;
    }

    container.innerHTML = events
        .map((event) => (
            `<span class="app-inline-pill">${event.event_type_label || "事件"} · ${event.severity || "low"}</span>`
        ))
        .join("");
}

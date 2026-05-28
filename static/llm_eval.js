(function initLlmEvalPage() {
    if (document.body?.dataset.page !== "llm_eval") {
        return;
    }

    const bootstrap = window.APP_BOOTSTRAP || {};
    const profile = bootstrap.profile || {};

    const scenarioSelect = document.getElementById("llm-eval-scenario-select");
    const providerSelect = document.getElementById("llm-eval-provider-select");
    const speakerSelect = document.getElementById("llm-eval-speaker");
    const restrictionsInput = document.getElementById("llm-eval-restrictions");
    const customMessageInput = document.getElementById("llm-eval-custom-message");
    const runButton = document.getElementById("llm-eval-run-button");
    const status = document.getElementById("llm-eval-status");
    const summaryBox = document.getElementById("llm-eval-scenario-summary");
    const providerMeta = document.getElementById("llm-eval-provider-meta");
    const rawReply = document.getElementById("llm-eval-raw-reply");
    const safeTemplateReply = document.getElementById("llm-eval-safe-template-reply");
    const responseText = document.getElementById("llm-eval-response-text");
    const promptPreview = document.getElementById("llm-eval-prompt-preview");
    const scoreGrid = document.getElementById("llm-eval-score-grid");
    const riskList = document.getElementById("llm-eval-risks");
    const suggestionList = document.getElementById("llm-eval-suggestions");
    const strengthList = document.getElementById("llm-eval-strengths");

    const fields = {
        name: document.getElementById("llm-eval-profile-name"),
        age: document.getElementById("llm-eval-profile-age"),
        hometown: document.getElementById("llm-eval-profile-hometown"),
        family_info: document.getElementById("llm-eval-profile-family"),
        life_events: document.getElementById("llm-eval-profile-life-events"),
        preferences: document.getElementById("llm-eval-profile-preferences"),
        notes: document.getElementById("llm-eval-profile-notes")
    };

    const scoreLabels = {
        warmth_score: "温和度",
        clarity_score: "清楚度",
        dementia_suitability_score: "认知障碍适配度",
        safety_score: "安全性",
        caregiver_usefulness_score: "家属辅助价值",
        length_score: "长度控制",
        restricted_word_penalty: "限制词惩罚",
        overall_score: "综合评分"
    };

    let scenarios = [];

    function setStatus(text, kind = "") {
        if (!status) {
            return;
        }
        status.textContent = text;
        status.className = "status-pill";
        if (kind) {
            status.classList.add(kind);
        }
    }

    function escapeHtml(text) {
        return String(text || "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll("\"", "&quot;")
            .replaceAll("'", "&#39;");
    }

    function fillProfileForm(nextProfile) {
        fields.name.value = nextProfile.name || "";
        fields.age.value = nextProfile.age ?? "";
        fields.hometown.value = nextProfile.hometown || "";
        fields.family_info.value = nextProfile.family_info || "";
        fields.life_events.value = nextProfile.life_events || "";
        fields.preferences.value = nextProfile.preferences || "";
        fields.notes.value = nextProfile.notes || "";
    }

    function readProfileForm() {
        return {
            name: fields.name.value.trim(),
            age: fields.age.value.trim() ? parseInt(fields.age.value.trim(), 10) : null,
            hometown: fields.hometown.value.trim(),
            family_info: fields.family_info.value.trim(),
            life_events: fields.life_events.value.trim(),
            preferences: fields.preferences.value.trim(),
            notes: fields.notes.value.trim()
        };
    }

    function readRestrictions() {
        return String(restrictionsInput?.value || "")
            .split("\n")
            .map((item) => item.trim())
            .filter(Boolean);
    }

    function currentScenario() {
        return scenarios.find((scenario) => scenario.id === scenarioSelect?.value) || null;
    }

    function updateScenarioSummary(scenario) {
        if (!summaryBox || !scenario) {
            return;
        }
        summaryBox.innerHTML = `
            <strong>${escapeHtml(scenario.title || "当前场景")}</strong>
            <span>${escapeHtml(scenario.summary || "")}</span>
            <span>风险关注：${escapeHtml(scenario.risk_focus || "")}</span>
            <span>当前提问者：${scenario.speaker === "caregiver" ? "家属" : "患者"}</span>
        `;
        if (speakerSelect) {
            speakerSelect.value = scenario.speaker || "patient";
        }
    }

    function renderScoreGrid(evaluation) {
        if (!scoreGrid) {
            return;
        }
        const keys = [
            "warmth_score",
            "clarity_score",
            "dementia_suitability_score",
            "safety_score",
            "caregiver_usefulness_score",
            "length_score",
            "restricted_word_penalty",
            "overall_score"
        ];
        scoreGrid.innerHTML = keys.map((key) => `
            <article class="analysis-metric-card llm-eval-score-card">
                <span class="gentle-stat-label">${escapeHtml(scoreLabels[key] || key)}</span>
                <strong class="analysis-metric-value">${escapeHtml(String(evaluation?.[key] ?? "-"))}</strong>
            </article>
        `).join("");
    }

    function renderSimpleList(container, items, emptyText) {
        if (!container) {
            return;
        }
        const normalized = Array.isArray(items) ? items.filter(Boolean) : [];
        if (!normalized.length) {
            container.innerHTML = `<div class="soft-list-row"><span>${escapeHtml(emptyText)}</span></div>`;
            return;
        }
        container.innerHTML = normalized.map((item) => `
            <div class="soft-list-row"><span>${escapeHtml(String(item))}</span></div>
        `).join("");
    }

    function renderResult(data) {
        const provider = data.provider || {};
        const diagnostics = data.diagnostics || {};
        providerMeta.textContent = [
            `requested_provider：${provider.requested_provider || diagnostics.requested_provider || "-"}`,
            `actual_provider：${provider.actual_provider || diagnostics.actual_provider || "-"}`,
            `model：${provider.model || diagnostics.model || "-"}`,
            `fallback_used：${provider.fallback_used ? "是" : "否"}`,
            `fallback_reason：${provider.fallback_reason || "-"}`,
            `postprocess_used：${provider.postprocess_used ? "是" : "否"}`,
            `template_used：${provider.template_used ? "是" : "否"}`,
            `template_name：${provider.template_name || "-"}`,
            `detected_state：${provider.detected_state || "-"}`,
            `strategy：${provider.strategy || "-"}`,
            `response_time_ms：${provider.response_time_ms ?? "-"}`
        ].join(" | ");
        rawReply.textContent = data.raw_llm_reply || "没有原始模型回复，可能是 mock/template 或请求失败。";
        safeTemplateReply.textContent = data.safe_template_reply || data.postprocess_reply || "未使用安全模板或后处理。";
        responseText.textContent = data.final_assistant_reply || data.response_text || "模型没有返回文本。";
        promptPreview.textContent = data.prompt_preview || "";
        renderScoreGrid(data.evaluation || {});
        renderSimpleList(riskList, data.evaluation?.risk_flags, "当前没有明显风险提示。");
        renderSimpleList(suggestionList, data.evaluation?.improvement_suggestions, "当前没有额外改进建议。");
        renderSimpleList(strengthList, data.evaluation?.strengths, "当前还没有明显亮点。");
    }

    async function fetchScenarios() {
        const response = await fetch("/llm_eval/scenarios");
        if (!response.ok) {
            throw new Error("无法加载测试场景");
        }
        return response.json();
    }

    async function runPresetScenario() {
        const payload = {
            scenario_id: scenarioSelect.value,
            provider: providerSelect?.value || "deepseek",
            restrictions: readRestrictions(),
            profile: readProfileForm()
        };
        const response = await fetch("/llm_eval/run", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "预设测试失败");
        }
        return data;
    }

    async function runCustomScenario() {
        const activeScenario = currentScenario();
        const payload = {
            title: activeScenario?.title || "自定义测试",
            provider: providerSelect?.value || "deepseek",
            speaker: speakerSelect.value || "patient",
            user_message: customMessageInput.value.trim(),
            restrictions: readRestrictions(),
            profile: readProfileForm(),
            summary: activeScenario?.summary || "测试自定义输入在阿尔兹海默症陪伴与照护辅助场景中的适配度。",
            risk_focus: activeScenario?.risk_focus || "观察是否温和、低刺激，并在需要时提醒联系家属。"
        };
        const response = await fetch("/llm_eval/custom", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "自定义测试失败");
        }
        return data;
    }

    async function runCurrentTest() {
        if (!scenarioSelect?.value) {
            setStatus("请先选择一个测试场景。", "warning");
            return;
        }

        runButton.disabled = true;
        setStatus("测试中...", "warning");

        try {
            const data = customMessageInput.value.trim()
                ? await runCustomScenario()
                : await runPresetScenario();
            renderResult(data);
            setStatus("测试完成");
        } catch (error) {
            console.error(error);
            setStatus(error.message || "测试失败", "warning");
        } finally {
            runButton.disabled = false;
        }
    }

    async function initialize() {
        setStatus("加载场景中...", "warning");
        fillProfileForm(profile);

        try {
            const data = await fetchScenarios();
            scenarios = Array.isArray(data.scenarios) ? data.scenarios : [];

            scenarioSelect.innerHTML = scenarios.map((scenario) => `
                <option value="${escapeHtml(scenario.id)}">${escapeHtml(scenario.title)}</option>
            `).join("");

            restrictionsInput.value = Array.isArray(data.restricted_words)
                ? data.restricted_words.join("\n")
                : "";

            const initialScenario = currentScenario();
            if (initialScenario) {
                updateScenarioSummary(initialScenario);
            }

            providerMeta.textContent = Array.isArray(data.preferred_style_rules)
                ? `默认 provider：${providerSelect?.value || "deepseek"} | 推荐表达：${data.preferred_style_rules.slice(0, 4).join(" / ")}`
                : "尚未运行。";

            setStatus("准备就绪");
        } catch (error) {
            console.error(error);
            setStatus("加载失败", "warning");
        }
    }

    scenarioSelect?.addEventListener("change", () => {
        const scenario = currentScenario();
        if (scenario) {
            updateScenarioSummary(scenario);
        }
    });

    runButton?.addEventListener("click", runCurrentTest);
    initialize();
})();

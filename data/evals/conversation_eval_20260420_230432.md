# Conversation Eval Results

生成时间：2026-04-20T23:04:32

## 人工评估维度

- 当前输入是否被正确接住
- 是否自然
- 是否没有脚本腔
- 是否没有后台材料泄漏
- 是否符合 Alzheimer 陪伴场景

## Provider: `mock`

| case_id | case_type | input_text | fallback_used | model_reply |
| --- | --- | --- | --- | --- |
| clarification_001 | clarification | 那是谁 | no | 我换个说法接你这句。刚才那句说的是你女儿小雨在上海工作。 |
| clarification_002 | clarification | 你再说什么 | no | 这回我说得再直接一点。刚才那句说的是你以前喜欢热汤面。 |
| clarification_003 | clarification | 什么意思 | no | 我刚刚说的是我刚刚提到你以前在南京商场上班。 |
| need_request_001 | need_request | 我饿了 | no | 那先吃点东西更要紧。要不要先找点你平时顺口的东西？要是想到喜欢热汤，我们就先从那个开始。 |
| need_request_002 | need_request | 我累了 | no | 那先让自己松一松。先休息一下，等舒服点我们再聊。等缓过来，再说熟悉的人和事也不迟。 |
| need_request_003 | need_request | 我不舒服 | no | 那先让自己缓一缓。哪里不得劲，你只说一点点也行。先把这会儿安顿好，别的等会儿再说。 |
| memory_question_001 | memory_question | 我是谁 | no | 大家常叫你王阿姨。一听到这个称呼，脑子里最先冒出来的是谁？ |
| memory_question_002 | memory_question | 我女儿是谁 | no | 我这边记着女儿小雨在上海工作。这个人平时最常陪你做什么？ |
| memory_question_003 | memory_question | 我以前做什么的 | no | 我刚刚说的是刚刚那句。 |
| short_input_001 | short_input | 嗯 | no | 我刚刚想到的是女儿小雨在上海工作。 |
| short_input_002 | short_input | 哦 | no | 女儿小雨在上海工作，是你很熟的人。 |
| short_input_003 | short_input | 不知道 | no | 女儿小雨在上海工作这件事，我们可以接着说。 |
| emotional_001 | emotional | 你在说什么 | no | 我刚刚提到的是我刚刚提到你以前喜欢下班后喝热汤。 |
| emotional_002 | emotional | 你是不是弄错了 | no | 你现在最想听清哪一句，我就接那一句。 |
| emotional_003 | emotional | 我是不是忘了什么 | no | 我刚刚提到的是刚刚那句。 |

## Provider: `zhipu`

| case_id | case_type | input_text | fallback_used | model_reply |
| --- | --- | --- | --- | --- |
| clarification_001 | clarification | 那是谁 | yes | 刚才那句说的是你女儿小雨在上海工作。 |
| clarification_002 | clarification | 你再说什么 | yes | 我刚刚提到的是你以前喜欢热汤面。 |
| clarification_003 | clarification | 什么意思 | yes | 我刚刚提到的是我刚刚提到你以前在南京商场上班。 |
| need_request_001 | need_request | 我饿了 | yes | 先让自己垫一口吧。要不要先找点你平时顺口的东西？要是想到喜欢热汤，我们就先从那个开始。 |
| need_request_002 | need_request | 我累了 | yes | 那先歇一歇。要不要先靠一会儿，我们等会儿再接着说。等缓过来，再说熟悉的人和事也不迟。 |
| need_request_003 | need_request | 我不舒服 | yes | 先把眼前这会儿照顾好。你想先缓一缓，还是先喝点水？先把这会儿安顿好，别的等会儿再说。 |
| memory_question_001 | memory_question | 我是谁 | yes | 大家常叫你王阿姨。要不就从这个称呼带出来的人说起。 |
| memory_question_002 | memory_question | 我女儿是谁 | yes | 我这边记着女儿小雨在上海工作。这个人平时最常陪你做什么？ |
| memory_question_003 | memory_question | 我以前做什么的 | yes | 刚才那句说的是刚刚那句。 |
| short_input_001 | short_input | 嗯 | yes | 女儿小雨在上海工作，是你很熟的人。 |
| short_input_002 | short_input | 哦 | yes | 女儿小雨在上海工作这件事，我们可以接着说。 |
| short_input_003 | short_input | 不知道 | yes | 女儿小雨在上海工作，是你很熟的人。 |
| emotional_001 | emotional | 你在说什么 | yes | 刚才那句说的是我刚刚提到你以前喜欢下班后喝热汤。 |
| emotional_002 | emotional | 你是不是弄错了 | yes | 你现在最想听清哪一句，我就接那一句。 |
| emotional_003 | emotional | 我是不是忘了什么 | yes | 我刚刚说的是刚刚那句。 |

## Provider: `deepseek`

| case_id | case_type | input_text | fallback_used | model_reply |
| --- | --- | --- | --- | --- |
| clarification_001 | clarification | 那是谁 | yes | 我换个说法接你这句。我刚刚提到的是你女儿小雨在上海工作。 |
| clarification_002 | clarification | 你再说什么 | yes | 我刚刚提到的是你以前喜欢热汤面。 |
| clarification_003 | clarification | 什么意思 | yes | 我刚刚说的是我刚刚提到你以前在南京商场上班。 |
| need_request_001 | need_request | 我饿了 | yes | 那先顾着肚子。想吃点热的，还是先喝口水？要是想到喜欢热汤，我们就先从那个开始。 |
| need_request_002 | need_request | 我累了 | yes | 先坐稳一点，缓口气。先休息一下，等舒服点我们再聊。等缓过来，再说熟悉的人和事也不迟。 |
| need_request_003 | need_request | 我不舒服 | yes | 先把眼前这会儿照顾好。哪里不得劲，你只说一点点也行。先把这会儿安顿好，别的等会儿再说。 |
| memory_question_001 | memory_question | 我是谁 | yes | 我这边记着别人叫你王阿姨。一听到这个称呼，脑子里最先冒出来的是谁？ |
| memory_question_002 | memory_question | 我女儿是谁 | yes | 在我这里留着的线索是女儿小雨在上海工作。要不就从这个人说起。 |
| memory_question_003 | memory_question | 我以前做什么的 | yes | 我刚刚提到的是刚刚那句。 |
| short_input_001 | short_input | 嗯 | yes | 我刚刚想到的是女儿小雨在上海工作。 |
| short_input_002 | short_input | 哦 | yes | 我刚刚想到的是女儿小雨在上海工作。 |
| short_input_003 | short_input | 不知道 | yes | 我刚刚想到的是女儿小雨在上海工作。 |
| emotional_001 | emotional | 你在说什么 | yes | 刚才那句说的是我刚刚提到你以前喜欢下班后喝热汤。 |
| emotional_002 | emotional | 你是不是弄错了 | yes | 你要是嫌我刚刚说得虚了，我们就换成眼前这会儿的话。 |
| emotional_003 | emotional | 我是不是忘了什么 | yes | 我刚刚说的是刚刚那句。 |

## Provider: `openai`

| case_id | case_type | input_text | fallback_used | model_reply |
| --- | --- | --- | --- | --- |
| clarification_001 | clarification | 那是谁 | yes | 这回我说得再直接一点。我刚刚提到的是你女儿小雨在上海工作。 |
| clarification_002 | clarification | 你再说什么 | yes | 我换个说法接你这句。我刚刚提到的是你以前喜欢热汤面。 |
| clarification_003 | clarification | 什么意思 | yes | 刚才那句说的是我刚刚提到你以前在南京商场上班。 |
| need_request_001 | need_request | 我饿了 | yes | 那先顾着肚子。要不要先找点你平时顺口的东西？要是想到喜欢热汤，我们就先从那个开始。 |
| need_request_002 | need_request | 我累了 | yes | 先坐稳一点，缓口气。先休息一下，等舒服点我们再聊。等缓过来，再说熟悉的人和事也不迟。 |
| need_request_003 | need_request | 我不舒服 | yes | 那先让自己缓一缓。哪里不得劲，你只说一点点也行。先把这会儿安顿好，别的等会儿再说。 |
| memory_question_001 | memory_question | 我是谁 | yes | 我这边记着别人叫你王阿姨。这个称呼一出来，你先想到的是谁？ |
| memory_question_002 | memory_question | 我女儿是谁 | yes | 我这边记着女儿小雨在上海工作。这个人平时最常陪你做什么？ |
| memory_question_003 | memory_question | 我以前做什么的 | yes | 我刚刚说的是刚刚那句。 |
| short_input_001 | short_input | 嗯 | yes | 女儿小雨在上海工作，是你很熟的人。 |
| short_input_002 | short_input | 哦 | yes | 女儿小雨在上海工作这件事，我们可以接着说。 |
| short_input_003 | short_input | 不知道 | yes | 女儿小雨在上海工作这件事，我们可以接着说。 |
| emotional_001 | emotional | 你在说什么 | yes | 刚才那句说的是我刚刚提到你以前喜欢下班后喝热汤。 |
| emotional_002 | emotional | 你是不是弄错了 | yes | 你要是嫌我刚刚说得虚了，我们就换成眼前这会儿的话。 |
| emotional_003 | emotional | 我是不是忘了什么 | yes | 我刚刚提到的是刚刚那句。 |

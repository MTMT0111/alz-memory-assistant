"""Central phrase configuration for the Alzheimer companion style engine.

The goal of this module is to keep the conversational tone easy to tune in one
place. The style engine should choose from these phrase sets, not scatter
literal strings across branching logic.
"""

from __future__ import annotations

from typing import Final

SOFT_MARKERS: Final[tuple[str, ...]] = (
    "没关系",
    "慢慢来",
    "不着急",
    "想不起来也没关系",
    "不知道也没关系",
)

CLARIFICATION_OPENINGS: Final[tuple[str, ...]] = (
    "我换短一点说。",
    "我重说一句。",
    "那我说得更直白一点。",
)

CLARIFICATION_ENDINGS: Final[tuple[str, ...]] = (
    "你听到哪一句，我们就接哪一句。",
    "你要是想听慢一点，我就慢一点说。",
    "这次我就只说这一句。",
)

CURRENT_NEED_OPENINGS: Final[dict[str, tuple[str, ...]]] = {
    "hungry": (
        "那先顾着肚子。",
        "那先吃点东西更要紧。",
        "先让自己垫一口吧。",
    ),
    "tired": (
        "那先歇一歇。",
        "那先让自己松一松。",
        "先坐稳一点，缓口气。",
    ),
    "sleepy": (
        "那就先顺着困意歇会儿。",
        "困了就先休息一会儿。",
        "那先准备歇一歇。",
    ),
    "discomfort": (
        "那先顾着舒服一点。",
        "那先让自己缓一缓。",
        "先把眼前这会儿照顾好。",
    ),
    "food": (
        "那先想着吃点什么。",
        "那先挑个顺口的东西。",
        "先说说你现在想吃什么。",
    ),
}

CURRENT_NEED_FOLLOWS: Final[dict[str, tuple[str, ...]]] = {
    "hungry": (
        "想吃点热的，还是先喝口水？",
        "你想先吃口软一点的，还是先喝点热的？",
        "要不要先找点你平时顺口的东西？",
    ),
    "tired": (
        "要不要先靠一会儿，我们等会儿再接着说。",
        "你想先坐一坐，还是先闭眼歇会儿？",
        "先休息一下，等舒服点我们再聊。",
    ),
    "sleepy": (
        "想先躺一会儿，还是先把灯光放轻一点？",
        "要不要先歇会儿，醒了我们再说。",
        "你先顺着这个困劲歇一下也好。",
    ),
    "discomfort": (
        "是想先坐一会儿，还是先叫身边的人来看看？",
        "你想先缓一缓，还是先喝点水？",
        "哪里不得劲，你只说一点点也行。",
    ),
    "food": (
        "你现在最想吃软一点的，还是热一点的？",
        "想到什么顺口的，就先说那个。",
        "要不要先从你平时爱吃的东西里挑一样？",
    ),
}

CURRENT_NEED_LIGHT_MEMORY: Final[dict[str, tuple[str, ...]]] = {
    "hungry": (
        "要是你平时有爱吃的那一口，我们就先说那个。",
        "想到家里常做的那样吃的，也可以先说出来。",
        "",
    ),
    "food": (
        "你平时顺口的那样东西，先说出来也好。",
        "要是想到家里常吃的味道，我们就从那个说起。",
        "",
    ),
    "tired": (
        "等缓过来，再说熟悉的人和事也不迟。",
        "",
    ),
    "sleepy": (
        "等你醒一醒，我们再慢慢说。",
        "",
    ),
    "discomfort": (
        "先把这会儿安顿好，别的等会儿再说。",
        "",
    ),
}

COMMENT_ACKNOWLEDGEMENTS: Final[tuple[str, ...]] = (
    "是啊，",
    "对，",
    "嗯，",
)

COMMENT_RESPONSES: Final[tuple[str, ...]] = (
    "那时候听起来确实挺像样的。",
    "听着就知道，那会儿这份工作挺体面。",
    "是，这样一说就能感觉出来那时条件不错。",
)

CLARIFICATION_DIRECT_PREFIXES: Final[tuple[str, ...]] = (
    "我刚刚说的是",
    "我刚刚提到的是",
    "刚才那句说的是",
)

OPENINGS: Final[tuple[str, ...]] = (
    "好。",
    "我记着。",
    "那我们接着说。",
    "行，我们往下聊。",
)

LIGHT_SUPPORT_OPENINGS: Final[dict[str, tuple[str, ...]]] = {
    "brief_ack": (
        "嗯。",
        "好。",
        "我接着听。",
        "那我们往下说。",
    ),
    "brief": (
        "嗯。",
        "好。",
        "我接着听。",
    ),
    "forgetful": (
        "一下子想不起也正常。",
        "这一会儿没想起来也行。",
        "先别急着把它想全。",
    ),
    "uncertain": (
        "一时说不上来也可以。",
        "先想到一点点就够了。",
        "先随口说一点也行。",
    ),
    "familiar": (
        "那就从熟悉的说起。",
        "我们先说最熟的那个人。",
        "先落到熟悉的人和事上。",
    ),
}

COMPLAINT_OPENINGS: Final[tuple[str, ...]] = (
    "那我多接你一句。",
    "那我换个更顺口的说法。",
    "行，我接得再实在一点。",
)

COMPLAINT_REPAIRS: Final[tuple[str, ...]] = (
    "你现在最想听清哪一句，我就接那一句。",
    "你要是嫌我刚刚说得虚了，我们就换成眼前这会儿的话。",
    "那我们不绕，先说你现在最在意的这件事。",
)

REPEAT_OPENINGS: Final[tuple[str, ...]] = (
    "这件事我们接着说。",
    "这个话题还在这儿。",
    "那就继续说这个。",
)

REPEAT_REPAIRS: Final[tuple[str, ...]] = (
    "我换个说法接你这句。",
    "这回我说得再直接一点。",
    "我不绕，接着你这句说。",
)

FAMILY_GUIDANCE: Final[tuple[str, ...]] = (
    "{anchor}，是你很熟的人。",
    "我刚刚想到的是{anchor}。",
    "{anchor}这件事，我们可以接着说。",
)

LIFE_GUIDANCE: Final[tuple[str, ...]] = (
    "那就先说{anchor}那段日子。",
    "可以先落在{anchor}这件事上。",
    "先接着{anchor}这段经历说。",
)

PREFERENCE_GUIDANCE: Final[tuple[str, ...]] = (
    "可以先说{anchor}。",
    "那就先聊{anchor}。",
    "先接着{anchor}这件事说。",
)

HOMETOWN_GUIDANCE: Final[tuple[str, ...]] = (
    "可以先说{anchor}。",
    "那就先说{anchor}这个地方。",
    "先落在{anchor}这处熟悉的地方上。",
)

GENERAL_GUIDANCE: Final[tuple[str, ...]] = (
    "先接着最熟的那件事说。",
    "先落在你最顺口的人或事上。",
    "就从你现在最想接的那一句开始。",
)

GENERAL_RECOVERY: Final[tuple[str, ...]] = (
    "你先说眼前最想接的那一句，我跟着你。",
    "就从你现在最想说的这件小事开始。",
    "你先落一句最顺口的话，我们就接那一句。",
)

SOFT_ENDINGS: Final[dict[str, tuple[str, ...]]] = {
    "default": (
        "你想到哪一点，我们就接哪一点。",
        "只要说出一点点就行。",
        "有一个小画面出来就很好。",
        "",
    ),
    "repeat": (
        "你先想起一点，我们就够往下接了。",
        "哪怕只是一件小事，也能接着聊。",
        "想起一点点，我们就顺着那一点往下走。",
    ),
    "complaint": (
        "你顺手接一句就行。",
        "你想到谁，就先说谁。",
        "先说出一个人名也可以。",
    ),
}

DIRECT_IDENTITY_OPENINGS: Final[tuple[str, ...]] = (
    "大家常叫你",
    "我这边记着别人叫你",
    "在我这里记着的称呼是",
)

DIRECT_IDENTITY_FOLLOWS: Final[tuple[str, ...]] = (
    "这个称呼一出来，你先想到的是谁？",
    "一听到这个称呼，脑子里最先冒出来的是谁？",
    "要不就从这个称呼带出来的人说起。",
)
DIRECT_IDENTITY_FALLBACK: Final[str] = "你想让我怎么叫你都行，我们就从那个称呼说起。"

DIRECT_AGE_OPENINGS: Final[tuple[str, ...]] = (
    "我记着你大概",
    "我这边留着的是",
    "在我这里记着的年纪是",
)

DIRECT_AGE_FOLLOWS: Final[tuple[str, ...]] = (
    "那会儿家里常是谁陪着你？",
    "那个年纪里，最常做的事是什么？",
    "那时候的日子，你先想到的是家里还是工作？",
)
DIRECT_AGE_FALLBACK: Final[str] = "年纪先放一边也行，我们先说说你更熟的人和日子。"

DIRECT_HOMETOWN_OPENINGS: Final[tuple[str, ...]] = (
    "你熟悉的地方是",
    "我记着你常说起的地方是",
    "在我这里留着的地方是",
)

DIRECT_HOMETOWN_FOLLOWS: Final[tuple[str, ...]] = (
    "那里你最先想到的是哪条路？",
    "那里有没有一家你总爱去的小店？",
    "一想到那里，你脑子里先出来的是什么地方？",
)
DIRECT_HOMETOWN_FALLBACK: Final[str] = "家乡先不用急着想全，想到哪一处就先说哪一处。"

DIRECT_FAMILY_OPENINGS: Final[tuple[str, ...]] = (
    "我记得",
    "我这边记着",
    "在我这里留着的线索是",
)

DIRECT_FAMILY_FOLLOWS: Final[tuple[str, ...]] = (
    "要不就从这个人说起。",
    "这个人平时最常陪你做什么？",
    "你先想到的，是和这个人在一起的哪件小事？",
)
DIRECT_FAMILY_FALLBACK: Final[str] = "家里人的线索还没记全，不过你想先从谁说起都可以。"

DIRECT_LIFE_OPENINGS: Final[tuple[str, ...]] = (
    "我记着你以前有过",
    "在我这里留着的经历里有",
    "我这边记得的一段日子是",
)

DIRECT_LIFE_FOLLOWS: Final[tuple[str, ...]] = (
    "那时候你身边最常见的是谁？",
    "那段日子里，你最熟的一件事是什么？",
    "你先想到的，是那时候的哪一幕？",
)
DIRECT_LIFE_FALLBACK: Final[str] = "以前的日子不用一下子想全，想到一点我们就从那一点说。"

DIRECT_PREFERENCE_OPENINGS: Final[tuple[str, ...]] = (
    "我记着你喜欢",
    "我这边留着的喜好里有",
    "在我这里记着的偏好里有",
)

DIRECT_PREFERENCE_FOLLOWS: Final[tuple[str, ...]] = (
    "那你最先想到的是哪一样？",
    "要不就从这个说起。",
    "这件事你以前常和谁一起做？",
)
DIRECT_PREFERENCE_FALLBACK: Final[str] = "喜欢的事最好聊，你想到什么我们就接着说什么。"

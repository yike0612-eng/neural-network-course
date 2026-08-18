function activationValue(type, z) {
  if (type === "relu") {
    return Math.max(0, z);
  }
  if (type === "tanh") {
    return Math.tanh(z);
  }
  return 1 / (1 + Math.exp(-z));
}

function updateNeuronLab() {
  const x1 = Number(document.getElementById("x1").value);
  const x2 = Number(document.getElementById("x2").value);
  const w1 = Number(document.getElementById("w1").value);
  const w2 = Number(document.getElementById("w2").value);
  const b = Number(document.getElementById("bias").value);
  const act = document.getElementById("activation").value;

  const z = x1 * w1 + x2 * w2 + b;
  const y = activationValue(act, z);

  const eq = `z = ${x1.toFixed(2)}*${w1.toFixed(2)} + ${x2.toFixed(2)}*(${w2.toFixed(2)}) + ${b.toFixed(2)} = ${z.toFixed(3)}`;
  const out = `y = ${act}(${z.toFixed(3)}) = ${y.toFixed(3)}`;

  document.getElementById("eq").textContent = eq;
  document.getElementById("out").textContent = out;

  let meter;
  if (act === "tanh") {
    meter = (y + 1) / 2;
  } else {
    meter = Math.max(0, Math.min(1, y));
  }
  document.getElementById("meter-bar").style.width = `${(meter * 100).toFixed(1)}%`;

  const hint = document.getElementById("hint");
  if (Math.abs(z) < 0.2) {
    hint.textContent = "当前 z 接近 0，模型处于决策边界附近。";
  } else if (z > 0) {
    hint.textContent = "当前 z 为正，神经元倾向输出更高激活值。";
  } else {
    hint.textContent = "当前 z 为负，神经元倾向抑制输出。";
  }
}

function animateNetwork() {
  const nodes = Array.from(document.querySelectorAll(".node.center"));
  let i = 0;
  setInterval(() => {
    nodes.forEach((n) => n.classList.remove("active"));
    nodes[i % nodes.length].classList.add("active");
    i += 1;
  }, 900);
}

function bindQuiz() {
  const btn = document.getElementById("check-answer");
  const result = document.getElementById("quiz-result");

  btn.addEventListener("click", () => {
    const selected = document.querySelector("input[name='q1']:checked");
    if (!selected) {
      result.textContent = "请先选择一个答案。";
      result.style.color = "#9b5200";
      return;
    }

    if (selected.value === "b") {
      result.textContent = "回答正确：梯度为正时，参数应向更小方向更新。";
      result.style.color = "#0c7c59";
    } else {
      result.textContent = "回答不正确：梯度下降会沿负梯度方向更新参数。";
      result.style.color = "#b00020";
    }
  });
}

const localCoach = {
  mode: "offline",
  label: "本地课程助教",
  topics: [
    {
      test: /神经元|输入层|隐藏层|输出层|权重|偏置/,
      answer: "可以把神经元看作一个小型计算单元：它先将每个输入乘以对应权重，再加上偏置，得到加权和 z。权重表示不同输入的重要程度，偏置让神经元即使输入全为 0 时也能移动判断起点。"
    },
    {
      test: /激活|relu|sigmoid|tanh/,
      answer: "激活函数为神经网络引入非线性。ReLU 会把负数压到 0，计算简单；Sigmoid 将结果压到 0 到 1 之间，适合表达概率直觉；Tanh 将结果压到 -1 到 1 之间且以 0 为中心。可在实验室切换三者，比较相同 z 对应的输出。"
    },
    {
      test: /梯度|下降|反向传播|更新/,
      answer: "梯度描述损失随参数微小变化的方向与速度。为了减小损失，梯度下降沿负梯度方向更新参数：参数新值 = 参数旧值 − 学习率 × 梯度。反向传播则高效地把误差信号从输出层逐层传回，用于计算各参数的梯度。"
    },
    {
      test: /损失|误差|学习|训练/,
      answer: "训练的目标不是直接记住答案，而是让预测值与真实值之间的损失逐步变小。每轮训练通常包括前向传播得到预测、计算损失、反向传播计算梯度、再更新权重四步。验证集可用于检查模型是否只是在记忆训练数据。"
    },
    {
      test: /过拟合|泛化|数据|模型/,
      answer: "过拟合是指模型在训练数据上表现很好，却难以处理新样本。可通过增加有代表性的数据、保留验证集、简化模型、正则化或提前停止训练来改善。模型输出需要结合数据质量与使用情境判断，而不能被当作绝对事实。"
    },
    {
      test: /deepseek|api|密钥|key|联网|大模型/,
      answer: "当前页面运行的是本地课程助教，不会连接 DeepSeek 或发送你的问题。日后如需接入真实模型，应把 API Key 保存于服务端环境变量，由服务端转发请求；不要把密钥写进 HTML、JavaScript 或公开仓库。"
    }
  ]
};

function getCurrentLabExplanation() {
  const x1 = Number(document.getElementById("x1").value);
  const x2 = Number(document.getElementById("x2").value);
  const w1 = Number(document.getElementById("w1").value);
  const w2 = Number(document.getElementById("w2").value);
  const bias = Number(document.getElementById("bias").value);
  const activation = document.getElementById("activation").value;
  const z = x1 * w1 + x2 * w2 + bias;
  const y = activationValue(activation, z);
  const direction = z > 0 ? "正" : z < 0 ? "负" : "零";

  return `当前实验中，z = ${z.toFixed(3)}，属于${direction}值；经过 ${activation} 后，输出 y = ${y.toFixed(3)}。其中 x1×w1 = ${(x1 * w1).toFixed(3)}，x2×w2 = ${(x2 * w2).toFixed(3)}，再加上偏置 ${bias.toFixed(3)}。试着只改变一个权重，观察 z 与 y 是否同步变化，并思考激活函数如何改变这种关系。`;
}

function getCoachAnswer(question) {
  const normalized = question.trim().toLowerCase();
  if (!normalized) {
    return "请输入一个与神经网络相关的问题，或选择上方的快捷问题。";
  }
  if (/当前|实验|参数|z|y/.test(normalized)) {
    return getCurrentLabExplanation();
  }

  const matchedTopic = localCoach.topics.find((topic) => topic.test.test(normalized));
  if (matchedTopic) {
    return matchedTopic.answer;
  }
  return "我目前是离线课程助教，重点覆盖神经元、激活函数、损失、梯度下降、反向传播与过拟合。你可以换一种说法，或点击快捷问题继续学习。";
}

function showCoachAnswer(question) {
  const answer = getCoachAnswer(question);
  const result = document.getElementById("coach-response");
  const questionLine = question.trim() ? `你的问题：${question.trim()}` : "离线助教提示";
  const questionElement = document.createElement("p");
  const answerElement = document.createElement("p");
  questionElement.className = "coach-question";
  questionElement.textContent = questionLine;
  answerElement.textContent = answer;
  result.replaceChildren(questionElement, answerElement);
  result.classList.add("visible");
}

function bindStudyCoach() {
  const form = document.getElementById("coach-form");
  const input = document.getElementById("coach-input");
  const currentLabButton = document.getElementById("explain-current-lab");
  const quickQuestions = document.querySelectorAll("[data-coach-question]");

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    showCoachAnswer(input.value);
  });

  quickQuestions.forEach((button) => {
    button.addEventListener("click", () => {
      const question = button.dataset.coachQuestion;
      input.value = question;
      showCoachAnswer(question);
    });
  });

  currentLabButton.addEventListener("click", () => {
    input.value = "请解释当前实验参数";
    showCoachAnswer(input.value);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const controls = ["x1", "x2", "w1", "w2", "bias", "activation"];
  controls.forEach((id) => {
    document.getElementById(id).addEventListener("input", updateNeuronLab);
  });

  updateNeuronLab();
  animateNetwork();
  bindQuiz();
  bindStudyCoach();
});

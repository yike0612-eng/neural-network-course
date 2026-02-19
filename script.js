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

document.addEventListener("DOMContentLoaded", () => {
  const controls = ["x1", "x2", "w1", "w2", "bias", "activation"];
  controls.forEach((id) => {
    document.getElementById(id).addEventListener("input", updateNeuronLab);
  });

  updateNeuronLab();
  animateNetwork();
  bindQuiz();
});

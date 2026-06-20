const API_BASE = "/api";
let currentEmail = "";
let trendChart, categoryChart;

const sessionForm = document.getElementById("session-form");
const setupStatus = document.getElementById("setup-status");
const questionsSection = document.getElementById("questions-section");
const questionsList = document.getElementById("questions-list");
const loadPerfBtn = document.getElementById("load-performance");
const perfSummary = document.getElementById("performance-summary");

sessionForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  setupStatus.textContent = "Generating questions...";

  const payload = {
    name: document.getElementById("name").value || null,
    email: document.getElementById("email").value,
    job_title: document.getElementById("job-title").value,
    job_description: document.getElementById("job-description").value,
    num_questions: parseInt(document.getElementById("num-questions").value, 10),
  };
  currentEmail = payload.email;

  try {
    const res = await fetch(`${API_BASE}/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(await res.text());
    const session = await res.json();
    setupStatus.textContent = `Session #${session.id} ready.`;
    renderQuestions(session.questions);
  } catch (err) {
    setupStatus.textContent = `Error: ${err.message}`;
  }
});

function renderQuestions(questions) {
  questionsSection.classList.remove("hidden");
  questionsList.innerHTML = "";

  questions.forEach((q) => {
    const card = document.createElement("div");
    card.className = "question-card";
    card.innerHTML = `
      <p class="question-text"><strong>[${q.category || "general"} / ${q.difficulty || "n/a"}]</strong> ${q.text}</p>
      <textarea rows="4" placeholder="Type your answer..."></textarea>
      <button>Submit Answer</button>
      <div class="evaluation"></div>
    `;
    const textarea = card.querySelector("textarea");
    const button = card.querySelector("button");
    const evalDiv = card.querySelector(".evaluation");

    button.addEventListener("click", async () => {
      button.disabled = true;
      evalDiv.textContent = "Evaluating...";
      try {
        const res = await fetch(`${API_BASE}/questions/${q.id}/answers`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ answer_text: textarea.value }),
        });
        if (!res.ok) throw new Error(await res.text());
        const answer = await res.json();
        const ev = answer.evaluation;
        const rubricLines = Object.entries(ev.rubric_scores)
          .map(([k, v]) => `${k}: ${v}/5`)
          .join(" | ");
        evalDiv.innerHTML = `
          <p><strong>Score: ${ev.overall_score}/10</strong></p>
          <p>${rubricLines}</p>
          <p>${ev.feedback}</p>
        `;
      } catch (err) {
        evalDiv.textContent = `Error: ${err.message}`;
      } finally {
        button.disabled = false;
      }
    });

    questionsList.appendChild(card);
  });
}

loadPerfBtn.addEventListener("click", async () => {
  const email = currentEmail || document.getElementById("email").value;
  if (!email) {
    perfSummary.textContent = "Generate a session first (or enter an email above).";
    return;
  }
  try {
    const res = await fetch(`${API_BASE}/users/${encodeURIComponent(email)}/performance`);
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    renderPerformance(data);
  } catch (err) {
    perfSummary.textContent = `Error: ${err.message}`;
  }
});

function renderPerformance(data) {
  perfSummary.innerHTML = `
    <p>Overall average score: ${data.overall_average !== null ? data.overall_average.toFixed(2) : "N/A"}</p>
    <p>Sessions: ${data.total_sessions} | Answers scored: ${data.total_answers}</p>
  `;

  const trendCtx = document.getElementById("trend-chart");
  const categoryCtx = document.getElementById("category-chart");

  if (trendChart) trendChart.destroy();
  if (categoryChart) categoryChart.destroy();

  trendChart = new Chart(trendCtx, {
    type: "line",
    data: {
      labels: data.trend.map((t) => `#${t.session_id} ${t.job_title}`),
      datasets: [
        {
          label: "Average score per session",
          data: data.trend.map((t) => t.average_score),
          borderColor: "#4f46e5",
          tension: 0.3,
        },
      ],
    },
    options: { scales: { y: { min: 0, max: 10 } } },
  });

  categoryChart = new Chart(categoryCtx, {
    type: "bar",
    data: {
      labels: data.category_breakdown.map((c) => c.category),
      datasets: [
        {
          label: "Average rubric score",
          data: data.category_breakdown.map((c) => c.average_score),
          backgroundColor: "#22c55e",
        },
      ],
    },
    options: { scales: { y: { min: 0, max: 5 } } },
  });
}

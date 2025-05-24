document.getElementById("jobFetchForm").addEventListener("submit", async function (e) {
  e.preventDefault();

  const form = e.target;
  const submitBtn = document.getElementById("submitBtn");
  const btnText = document.getElementById("btnText");
  const btnLoader = document.getElementById("btnLoader");
  const loading = document.getElementById("loading");
  const jobResults = document.getElementById("jobResults");

  // Show loading state
  submitBtn.disabled = true;
  btnText.style.display = "none";
  btnLoader.style.display = "flex";
  loading.style.display = "block";
  jobResults.style.display = "none";
  jobResults.innerHTML = ""; // Clear previous results

  try {
    const formData = new FormData(form);
    const response = await fetch("http://127.0.0.1:5000/api/fetch-linkedin-jobs", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Error: ${response.status}`);
    }

    const result = await response.json();

    if (result.success) {
      result.jobs.forEach((job) => {
        const jobCard = document.createElement("div");
        jobCard.className = "job-card";
        jobCard.innerHTML = `
          <h4>${job.title}</h4>
          <p><strong>Company:</strong> ${job.company}</p>
          <p><strong>Location:</strong> ${job.location}</p>
          <p><strong>Description:</strong> ${job.description}</p>
          <a href="${job.url}" target="_blank">View Job</a>
        `;
        jobResults.appendChild(jobCard);
      });

      jobResults.style.display = "block";
      jobResults.scrollIntoView({ behavior: "smooth" });
    } else {
      jobResults.innerHTML = `<p>No jobs found for the given criteria. Please try again.</p>`;
      jobResults.style.display = "block";
    }
  } catch (error) {
    jobResults.innerHTML = `<p style="color: var(--error);">An error occurred: ${error.message}</p>`;
    jobResults.style.display = "block";
  } finally {
    // Hide loading state
    loading.style.display = "none";
    btnText.style.display = "flex";
    btnLoader.style.display = "none";
    submitBtn.disabled = false;
  }
});

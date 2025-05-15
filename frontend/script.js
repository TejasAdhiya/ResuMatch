document.getElementById("uploadForm").addEventListener("submit", async function (e) {
  e.preventDefault();

  // Form data
  const formData = new FormData();
  const resumeFile = document.getElementById("resume").files[0];
  const jobDescription = document.getElementById("jobDescription").value;

  formData.append("file", resumeFile);
  formData.append("job_description", jobDescription);

  try {
    // Send POST request to FastAPI backend
    const response = await fetch("http://127.0.0.1:8000/api/upload-resume", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error("Failed to fetch results. Please check the backend.");
    }

    const result = await response.json();

    // Display results
    document.getElementById("result").style.display = "block";
    document.getElementById("similarityScore").textContent = result.similarity_score;
    document.getElementById("matchedKeywords").textContent = result.matched_keywords.join(", ");
    document.getElementById("missingKeywords").textContent = result.missing_keywords.join(", ");
    document.getElementById("suggestions").textContent = result.suggestion;

  } catch (error) {
    alert("Error: " + error.message);
  }
});

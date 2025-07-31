document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("uploadForm");
  const results = document.getElementById("results");
  const dataBody = document.getElementById("dataBody");
  const spinner = document.getElementById("spinner");
  const toast = document.getElementById("toast");
  const downloadBtn = document.getElementById("downloadBtn");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    dataBody.innerHTML = "";
    results.classList.add("hidden");
    spinner.classList.remove("hidden");

    const formData = new FormData();
    const fileInput = document.getElementById("pdfFile");
    const urlInput = document.getElementById("reportUrl");

    // if (fileInput.files.length > 0) {
    //   formData.append("pdfFile", fileInput.files[0]);
    // }
    if (fileInput.files.length > 0) {
  for (let i = 0; i < fileInput.files.length; i++) {
    formData.append("pdfFile", fileInput.files[i]);
  }
}

     formData.append("reportUrl", urlInput.value.trim());

    try {
      const response = await fetch("/extract", {
        method: "POST",
        body: formData
      });

      const result = await response.json();
      spinner.classList.add("hidden");

      if (result.status === "success") {
        showToast("✅ Extraction successful!");
        results.classList.remove("hidden");
        dataBody.innerHTML = "";

        result.data.forEach(row => {
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td>${row.company}</td>
            <td>${row.year}</td>
            <td>${row.budget}</td>
            <td>${row.theme}</td>
            <td>${row.eduBudget}</td>
            <td>${row.beneficiaries}</td>
            <td>${row.type}</td>
            <td>${row.literacy}</td>
            <td>${row.intervention}</td>
            <td>${row.projects}</td>
            <td>${row.location}</td>
            <td>${row.partners}</td>
            <td>${row.scheme}</td>
            <td>${row.outcome}</td>
          `;
          dataBody.appendChild(tr);
        });
      } else {
        showToast("❌ Error extracting data");
      }

    } catch (err) {
      spinner.classList.add("hidden");
      showToast("❌ Network error");
      console.error("Error:", err);
    }
  });

  // 📥 Download Excel Button
  downloadBtn.addEventListener("click", () => {
    window.location.href = "/download-excel";
  });

  // ✅ Toast Function
  function showToast(msg) {
    toast.innerText = msg;
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), 3000);
  }
});

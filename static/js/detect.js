document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("image-input");
  const preview = document.getElementById("preview");
  const noPreview = document.getElementById("no-preview");
  const identifyBtn = document.getElementById("identify-btn");
  const newIdentBtn = document.getElementById("new-ident-btn");

  const resultCard = document.getElementById("result-card");
  const resultImage = document.getElementById("result-image");
  const resultName = document.getElementById("result-name");
  const resultConfidence = document.getElementById("result-confidence");
  const careLight = document.getElementById("care-light");
  const careWater = document.getElementById("care-water");
  const careSoil = document.getElementById("care-soil");
  const careNotes = document.getElementById("care-notes");

  // Hide result card initially
  resultCard.style.display = "none";

  // -------- IMAGE PREVIEW --------
  input.addEventListener("change", () => {
    const file = input.files && input.files[0];
    if (!file) {
      preview.style.display = "none";
      noPreview.style.display = "block";
      return;
    }

    const url = URL.createObjectURL(file);
    preview.src = url;
    preview.style.display = "block";
    noPreview.style.display = "none";
  });

  // -------- IDENTIFY PLANT --------
  identifyBtn.addEventListener("click", async () => {
    const file = input.files && input.files[0];
    if (!file) {
      alert("Please select an image first.");
      return;
    }

    identifyBtn.disabled = true;
    identifyBtn.textContent = "Identifying...";

    const formData = new FormData();
    formData.append("image", file);

    try {
      const res = await fetch("/upload", {
        method: "POST",
        body: formData
      });

      const data = await res.json();

      if (!data.ok) {
        alert(data.error || "Error identifying plant.");
      } else {
        const p = data.identification;

        // Update result card
        resultImage.src = p.image_url;
        resultImage.style.display = "block";

        resultName.textContent = p.common_name || p.plant_name;
        resultConfidence.textContent = Math.round(p.confidence * 100) + "% match";
        careLight.textContent = p.care_light;
        careWater.textContent = p.care_water;
        careSoil.textContent = p.care_soil;
        careNotes.textContent = p.care_notes;

        resultCard.style.display = "block";
      }
    } catch (err) {
      console.error(err);
      alert("Upload failed.");
    }

    identifyBtn.disabled = false;
    identifyBtn.textContent = "Identify";
  });

  // -------- RESET UI (NEW FEATURE) --------
  newIdentBtn.addEventListener("click", () => {
    // Clear file input
    input.value = "";

    // Reset preview
    preview.src = "";
    preview.style.display = "none";
    noPreview.style.display = "block";

    // Hide result card & clear values
    resultCard.style.display = "none";
    resultName.textContent = "";
    resultConfidence.textContent = "";
    careLight.textContent = "";
    careWater.textContent = "";
    careSoil.textContent = "";
    careNotes.textContent = "";
    resultImage.src = "";
    resultImage.style.display = "none";
  });
});

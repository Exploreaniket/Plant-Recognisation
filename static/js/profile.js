document.addEventListener("DOMContentLoaded", () => {
  const avatarImg = document.getElementById("avatar-display");
  const avatarInput = document.getElementById("avatar-file");
  const profileForm = document.getElementById("profile-form");

  if (!avatarImg || !avatarInput || !profileForm) return;

  // When user taps the avatar, open file picker
  avatarImg.addEventListener("click", () => {
    avatarInput.click();
  });

  // When a file is selected, preview and auto-submit form
  avatarInput.addEventListener("change", () => {
    const file = avatarInput.files && avatarInput.files[0];
    if (!file) return;

    // Preview the new image immediately
    const url = URL.createObjectURL(file);
    avatarImg.src = url;

    // Auto-submit the form so backend saves the new avatar
    profileForm.submit();
  });
});

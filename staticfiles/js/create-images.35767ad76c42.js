// Generic image preview + card state for Django forms or plain inputs
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.image-upload-card input[type="file"]').forEach((input) => {
    input.addEventListener('change', () => {
      const file = input.files && input.files[0];
      const card = input.closest('.image-upload-card');
      if (!card) return;
      const preview = card.querySelector('.image-preview');
      const icon = card.querySelector('.upload-icon');
      const txt = card.querySelector('.upload-text');
      const hint = card.querySelector('.upload-hint');
      if (file && preview) {
        const reader = new FileReader();
        reader.onload = (e) => {
          preview.src = e.target.result;
          preview.style.display = 'block';
          card.classList.add('has-image');
          if (icon) icon.style.display = 'none';
          if (txt) txt.style.display = 'none';
          if (hint) hint.style.display = 'none';
        };
        reader.readAsDataURL(file);
      }
    });
  });

  // Delete/reset button inside cards
  document.querySelectorAll('.image-upload-card .delete-btn').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const card = btn.closest('.image-upload-card');
      if (!card) return;
      const input = card.querySelector('input[type="file"]');
      const preview = card.querySelector('.image-preview');
      const icon = card.querySelector('.upload-icon');
      const txt = card.querySelector('.upload-text');
      const hint = card.querySelector('.upload-hint');
      if (input) input.value = '';
      if (preview) { preview.src = ''; preview.style.display = 'none'; }
      card.classList.remove('has-image');
      if (icon) icon.style.display = '';
      if (txt) txt.style.display = '';
      if (hint) hint.style.display = '';
    });
  });
});


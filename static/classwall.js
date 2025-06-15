
  // Auto-growing textarea
function autoGrow(element) {
    element.style.height = "auto";
    element.style.height = (element.scrollHeight) + "px";
}

// File upload feedback
document.addEventListener("DOMContentLoaded", () => {
    // File upload display
    const fileInput = document.getElementById('media-upload');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            const fileName = this.files[0]?.name || '';
            document.getElementById('file-name').textContent = fileName;
        });
    }

    // Submit button loading state
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.innerHTML = '<span class="loading-spinner"></span> Posting...';
                submitBtn.disabled = true;
            }
        });
    });

    // Smooth scrolling to new posts
    if (window.location.hash === '#new-post') {
        const postForm = document.querySelector('.post-form');
        if (postForm) {
            postForm.scrollIntoView({ behavior: 'smooth' });
            const textarea = postForm.querySelector('textarea');
            if (textarea) textarea.focus();
        }
    }
});

document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.comment-input').forEach(input => {
        input.addEventListener('input', function () {
            const value = this.value;
            const caret = this.selectionStart;
            const atIndex = value.lastIndexOf('@', caret);
            const dropdown = this.nextElementSibling;

            if (atIndex > -1 && !value.substring(atIndex, caret).includes(' ')) {
                const term = value.substring(atIndex + 1, caret);
                if (term.length) {
                    fetch(`/get_parents?term=${encodeURIComponent(term)}&post_id=${this.dataset.postId}`)
                        .then(res => res.json())
                        .then(data => {
                            dropdown.innerHTML = data.map(p =>
                                `<div class="mention-option" data-username="${p.username}">@${p.username} (${p.name})</div>`
                            ).join('');
                            dropdown.style.display = 'block';
                        });
                } else {
                    dropdown.style.display = 'none';
                }
            } else {
                dropdown.style.display = 'none';
            }
        });

        input.addEventListener('keydown', function (e) {
            const dropdown = this.nextElementSibling;
            if (dropdown && dropdown.style.display === 'block' && e.key === 'Enter') {
                e.preventDefault();
                const option = dropdown.querySelector('.mention-option');
                if (option) {
                    selectMention(this, option);
                }
            }
        });

        document.addEventListener('click', function (e) {
            if (!e.target.closest('.mention-container')) {
                document.querySelectorAll('.mention-dropdown').forEach(d => d.style.display = 'none');
            }
        });
    });

    document.addEventListener('click', function (e) {
        if (e.target.classList.contains('mention-option')) {
            const option = e.target;
            const input = option.closest('.mention-container').querySelector('.comment-input');
            selectMention(input, option);
        }
    });

    function selectMention(input, option) {
        const val = input.value;
        const caretPos = input.selectionStart;
        const atIndex = val.lastIndexOf('@', caretPos);
        input.value = val.substring(0, atIndex) + '@' + option.dataset.username + ' ' + val.substring(caretPos);
        input.nextElementSibling.style.display = 'none';
        input.focus();
        input.selectionStart = input.selectionEnd = atIndex + option.dataset.username.length + 2;
    }
});

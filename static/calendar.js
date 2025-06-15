document.addEventListener("DOMContentLoaded", () => {
  const toggleButton = document.querySelector(".filter-toggle");
  const filterOptions = ["week", "month", "year"];
  const filterLabels = ["This Week", "This Month", "This Year"];
  const currentFilter = "{{ filter_type or 'month' }}";
  let currentIndex = filterOptions.indexOf(currentFilter);

  if (toggleButton) {
    toggleButton.textContent = filterLabels[currentIndex];

    toggleButton.addEventListener("click", () => {
      currentIndex = (currentIndex + 1) % filterOptions.length;
      const selectedFilter = filterOptions[currentIndex];
      window.location.href = `/calendar?filter=${selectedFilter}`;
    });
  }

  // Delete confirmation
  document.querySelectorAll('.delete-form').forEach(form => {
    form.addEventListener('submit', (e) => {
      if (!confirm('Are you sure you want to delete this event?')) {
        e.preventDefault();
      }
    });
  });
});

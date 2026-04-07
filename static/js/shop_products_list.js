document.addEventListener('DOMContentLoaded', function () {
  const searchInput = document.getElementById('shop-products-search');
  const clearButton = document.getElementById('shop-products-search-clear');
  const rows = Array.from(document.querySelectorAll('#shop-products-table tbody .shop-products-view__row'));

  if (!searchInput || !clearButton || !rows.length) {
    return;
  }

  const applyFilter = function () {
    const query = (searchInput.value || '').trim().toLowerCase();
    rows.forEach(function (row) {
      const content = (row.getAttribute('data-search') || '').toLowerCase();
      row.style.display = !query || content.includes(query) ? '' : 'none';
    });
  };

  searchInput.addEventListener('input', applyFilter);
  clearButton.addEventListener('click', function () {
    searchInput.value = '';
    applyFilter();
    searchInput.focus();
  });
});

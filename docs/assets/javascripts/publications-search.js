document.addEventListener("DOMContentLoaded", function () {
  var input = document.getElementById("pub-search");
  var table = document.getElementById("publications-table");

  if (!input || !table || !table.tBodies.length) {
    return;
  }

  var rows = Array.prototype.slice.call(table.tBodies[0].rows);

  function normalize(text) {
    return (text || "").toLowerCase();
  }

  function filterRows() {
    var query = normalize(input.value.trim());

    rows.forEach(function (row) {
      var rowText = normalize(row.textContent);
      var visible = query === "" || rowText.indexOf(query) !== -1;
      row.style.display = visible ? "" : "none";
    });
  }

  input.addEventListener("input", filterRows);
});

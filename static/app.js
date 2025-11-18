document.addEventListener('DOMContentLoaded', () => {
    fetchLogs();
});

function fetchLogs() {
    fetch('/api/logs')
        .then(response => response.json())
        .then(data => {
            const tableBody = document.querySelector('table tbody');
            tableBody.innerHTML = ''; // Clear "Loading..." row

            if (data.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="6" class="no-logs">No scan logs found.</td></tr>';
                return;
            }

            data.forEach(log => {
                const row = document.createElement('tr');
                if (log.reviewed) row.classList.add('is-reviewed');
                
                // Create violations list HTML
                let violationsHtml = '<span class="no-violations">--</span>';
                if (log.violations && log.violations.length > 0) {
                    violationsHtml = '<ul class="violations-list">' + 
                        log.violations.map(v => `<li>${v}</li>`).join('') + 
                        '</ul>';
                }

                // Action button HTML
                let actionHtml = '<span class="reviewed-text">Reviewed</span>';
                if (!log.reviewed) {
                    actionHtml = `<button class="review-btn" onclick="markAsReviewed(${log.id}, this)">Mark as Reviewed</button>`;
                }

                row.innerHTML = `
                    <td><span class="status status-${log.status.toLowerCase()}">${log.status}</span></td>
                    <td class="timestamp">${log.timestamp}</td>
                    <td class="file-path">${log.file_path}</td>
                    <td>${log.category}</td>
                    <td>${violationsHtml}</td>
                    <td class="action-cell">${actionHtml}</td>
                `;
                tableBody.appendChild(row);
            });
        })
        .catch(error => console.error('Error fetching logs:', error));
}

function markAsReviewed(logId, btnElement) {
    fetch(`/api/review/${logId}`, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const row = btnElement.closest('tr');
                row.classList.add('is-reviewed');
                btnElement.parentElement.innerHTML = '<span class="reviewed-text">Reviewed</span>';
            } else {
                alert('Failed to update status');
            }
        })
        .catch(error => console.error('Error:', error));
}
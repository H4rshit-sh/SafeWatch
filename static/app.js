// Wait for the entire HTML page to load before running the script
document.addEventListener('DOMContentLoaded', () => {

    // Find all buttons with the class '.review-btn'
    const reviewButtons = document.querySelectorAll('.review-btn');

    // Add a 'click' event listener to each button found
    reviewButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Get the log ID from the button's 'data-id' attribute
            const logId = button.dataset.id;
            
            // Call our 'markAsReviewed' function
            markAsReviewed(logId, button);
        });
    });
});

function markAsReviewed(logId, buttonElement) {
    // This is an asynchronous 'fetch' request to our Flask server.
    // It calls the '@app.route('/review/<int:log_id>', methods=['POST'])' endpoint.
    fetch(`/review/${logId}`, {
        method: 'POST', // We are sending data (or at least, making a change)
    })
    .then(response => {
        // Check if the server responded with 'OK' (status 200)
        if (response.ok) {
            return response.json(); // Parse the JSON response from Flask
        } else {
            // If the server had an error, throw an error
            throw new Error('Server responded with an error.');
        }
    })
    .then(data => {
        // 'data' is the {status: 'success'} object from Flask
        if (data.status === 'success') {
            console.log(data.message);
            
            // --- Update the UI without reloading the page ---
            
            const cell = buttonElement.parentElement;
            
            cell.innerHTML = '<span class="reviewed-text">Reviewed</span>';
            
            const row = buttonElement.closest('tr');
            if (row) {
                row.classList.add('is-reviewed');
            }
        } else {
            alert('Failed to mark as reviewed. Please check console.');
            console.error(data.message);
        }
    })
    .catch(error => {
        alert('An error occurred. Could not contact server.');
        console.error('Fetch Error:', error);
    });
}
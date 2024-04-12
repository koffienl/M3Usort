document.addEventListener('DOMContentLoaded', function() {
    var rebuildLink = document.getElementById('rebuild-link');
    var downloadLink = document.getElementById('download-link');
    var flashMessagesContainer = document.getElementById('flash-messages-container');

    // Function to hide flash messages
    function hideFlashMessagesAfterDelay() {
        const flashMessages = document.querySelectorAll('.flash-message');
        flashMessages.forEach(flashMessage => {
            // Check if the flashMessage does NOT have the 'no-hide' class
            if (!flashMessage.classList.contains('static')) {
                setTimeout(() => {
                    flashMessage.style.opacity = '0';
                    setTimeout(() => flashMessage.remove(), 600); // Wait for opacity transition, then remove
                }, 5000); // Hide after 5 seconds (5000ms)
            }
        });
    }
    

    // Hide existing server-side flash messages after delay
    hideFlashMessagesAfterDelay();

    if (rebuildLink) {
        rebuildLink.addEventListener('click', function(event) {
            event.preventDefault(); // Prevent the default link action

            // Create and append the client-side flash message
            var flashMessageDiv = document.createElement('div');
            flashMessageDiv.textContent = 'Rebuild process started. Please wait for completion.';
            flashMessageDiv.className = 'flash-message info'; // Adjust class name as needed
            flashMessagesContainer.appendChild(flashMessageDiv);

            // Hide the newly created flash message after delay
            hideFlashMessagesAfterDelay();


            // Redirect to the rebuild page after a short delay
            setTimeout(function() {
                window.location.href = '/rebuild'; // Adjust the URL as needed
            }, 200); // 2 seconds delay

        });
    }

    if (downloadLink) {
        downloadLink.addEventListener('click', function(event) {
            event.preventDefault(); // Prevent the default link action

            // Create and append the client-side flash message
            var flashMessageDiv = document.createElement('div');
            flashMessageDiv.textContent = 'Download process started. Please wait for completion.';
            flashMessageDiv.className = 'flash-message info'; // Adjust class name as needed
            flashMessagesContainer.appendChild(flashMessageDiv);

            // Hide the newly created flash message after delay
            hideFlashMessagesAfterDelay();


            // Redirect to the rebuild page after a short delay
            setTimeout(function() {
                window.location.href = '/download'; // Adjust the URL as needed
            }, 200); // 2 seconds delay

        });
    }




    const modal = document.getElementById("myModal");
    const modalText = document.getElementById("modal-text");
    const confirmBtn = document.getElementById("confirmBtn");
    const cancelBtn = document.getElementById("cancelBtn");
    const span = document.getElementsByClassName("close")[0];
    const restartlink = document.querySelectorAll('.restart-link');

    restartlink.forEach(link => {
        link.addEventListener('click', function() {
            modalText.innerHTML = `Are you sure you want to restart the server?`;
            modal.style.display = "block";
            
            confirmBtn.onclick = function() {

                var flashMessagesContainer = document.getElementById('flash-messages-container');


                // Create and append the client-side flash message
                var flashMessageDiv = document.createElement('div');
                flashMessageDiv.textContent = "Restarting server ...";
                flashMessageDiv.className = 'flash-message info'; // Adjust class name as needed
                flashMessagesContainer.appendChild(flashMessageDiv);
    
                // Hide the newly created flash message after delay
                hideFlashMessagesAfterDelay();


                console.log("Restarting ...");
                modal.style.display = "none";
                fetch('/restart', {
                    method: 'POST',
                    headers: {
                    }
                })
            

                // Call function to handle adding the movie
            };
        });
    });

    cancelBtn.onclick = function() {
        modal.style.display = "none";
    };

    span.onclick = function() {
        modal.style.display = "none";
    };

    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    };




});

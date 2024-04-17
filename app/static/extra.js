document.addEventListener('DOMContentLoaded', function () {
    const modal = document.getElementById("myModal");
    const modalText = document.getElementById("modal-text");
    const modalImage = document.getElementById("modal-image");
    const confirmBtn = document.getElementById("confirmBtn");
    const cancelBtn = document.getElementById("cancelBtn");
    const span = document.getElementsByClassName("close")[0];

    var rebuildLink = document.getElementById('rebuild-link');
    var downloadLink = document.getElementById('download-link');
    var restartLink = document.getElementById('restart-link');
    var updateLink = document.getElementById('update-link');
    //var flashMessagesContainer = document.getElementById('flash-messages-container');

    hideFlashMessagesAfterDelay();

    if (rebuildLink) {
        rebuildLink.addEventListener('click', function (event) {
            event.preventDefault(); // Prevent the default link action


            const obj = {
                message: "Rebuild process started. Please wait for completion.",
                type: "info",
            };
            const jsonString = JSON.stringify(obj);
            createAndDisplayFlashMessage(obj, "FlashRebuild");

            fetch('/rebuild', {
                method: 'GET',
                headers: {
                }
            })
                .then(response => response.json())  // Convert the response to JSON
                .then(data => {
                    console.log("data")
                    console.log(data)
                    removeFlashMessageById('FlashRebuild');
                    createAndDisplayFlashMessage(data);
                })
                .catch(error => {
                    console.error('Error:', error);
                });
        });
    }

    if (downloadLink) {
        downloadLink.addEventListener('click', function (event) {
            event.preventDefault(); // Prevent the default link action


            const obj = {
                message: "Download process started. Please wait for completion.",
                type: "info",
            };
            const jsonString = JSON.stringify(obj);
            createAndDisplayFlashMessage(obj, "FlashDownload");

            fetch('/download', {
                method: 'GET',
                headers: {
                }
            })
                .then(response => response.json())  // Convert the response to JSON
                .then(data => {
                    console.log("data")
                    console.log(data)
                    removeFlashMessageById('FlashDownload');
                    createAndDisplayFlashMessage(data);
                })
                .catch(error => {
                    console.error('Error:', error);
                });
        });
    }

    if (restartLink) {
        restartLink.addEventListener('click', function () {
            event.preventDefault(); // Prevent the default link action

            modalText.innerHTML = `Are you sure you want to restart the server?`;
            modalImage.innerHTML = "?"
            modal.style.display = "block";

            confirmBtn.onclick = function () {
                modal.style.display = "none";

                const obj = {
                    message: "Restart process started. Please wait for completion.",
                    type: "info",
                };
                const jsonString = JSON.stringify(obj);
                createAndDisplayFlashMessage(obj, "FlashRestart");

                fetch('/restart', {
                    method: 'POST'
                })
                sleepAndRefresh()
            };
        });
    }

    if (updateLink) {
        updateLink.addEventListener('click', function () {
            event.preventDefault(); // Prevent the default link action

            modalText.innerHTML = `Are you sure you want to update the server?`;
            modal.style.display = "block";

            confirmBtn.onclick = function () {
                modal.style.display = "none";

                const obj = {
                    message: "Update process started. Please wait for completion.",
                    type: "info",
                };
                const jsonString = JSON.stringify(obj);
                createAndDisplayFlashMessage(obj, "FlashUpdate");

                fetch('/update', {
                    method: 'POST'
                })
                sleepAndRefresh()
            };
        });
    }

    cancelBtn.onclick = function () {
        modal.style.display = "none";
    };

    span.onclick = function () {
        modal.style.display = "none";
    };

    window.onclick = function (event) {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    };

    function createAndDisplayFlashMessage(data, messageId) {
        var flashMessagesContainer = document.getElementById('flash-messages-container');

        // Create and append the client-side flash message
        var flashMessageDiv = document.createElement('div');
        if (messageId) {  // Check if an ID was provided
            flashMessageDiv.id = messageId;  // Set the unique ID for the flash message
        }
        flashMessageDiv.textContent = data.message;  // Using dynamic message
        flashMessageDiv.className = 'flash-message ' + data.type;  // Dynamic class based on type
        flashMessagesContainer.appendChild(flashMessageDiv);

        setTimeout(() => {
            flashMessageDiv.remove();
        }, 5000);
    }

    function sleepAndRefresh() {
        // Delay execution for 2000 milliseconds (2 seconds)
        setTimeout(function () {
            // Refresh the current page
            window.location.reload();
        }, 2000);
    }

    function removeFlashMessageById(messageId) {
        const messageElement = document.getElementById(messageId);
        if (messageElement) {
            messageElement.remove();
            console.log("Flash message removed:", messageId);
        } else {
            console.log("No flash message found with ID:", messageId);
        }
    }

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
});
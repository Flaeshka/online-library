function openLogin() {
    document.getElementById("loginModal").style.display = "flex";
}

function closeLogin() {
    document.getElementById("loginModal").style.display = "none";
}

const loginModal = document.getElementById("loginModal");

if (loginModal) {
    loginModal.addEventListener("click", function() {
        closeLogin();
    });
}
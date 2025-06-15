document.addEventListener('DOMContentLoaded', function () {
    const logoutButton = document.getElementById('logout');
    
    if (logoutButton) {
        logoutButton.addEventListener('click', function() {
            window.location.href = "/logout"; // Redirects to the logout route
        });
    }
});


  function toggleDropdown() {
    document.getElementById("profileDropdown").classList.toggle("show");
  }

  // Close dropdown if clicked outside
  window.onclick = function(event) {
    if (!event.target.matches('.profile-icon')) {
      let dropdowns = document.getElementsByClassName("dropdown-content");
      for (let i = 0; i < dropdowns.length; i++) {
        let openDropdown = dropdowns[i];
        if (openDropdown.classList.contains('show')) {
          openDropdown.classList.remove('show');
        }
      }
    }
  }



document.addEventListener("DOMContentLoaded", () => {
    const deleteButton = document.getElementById("delete");
    const confirmButton = document.getElementById("confirm-delete");
    const deleteMessage = document.getElementById("delete-message");
    const studentCards = document.querySelectorAll(".student-card");
    const studentLinks = document.querySelectorAll(".student-card-link");
    const selectedStudents = new Set();
    let deleteMode = false;

    // Toggle delete mode
    deleteButton.addEventListener("click", () => {
        deleteMode = !deleteMode; // Toggle the mode

        if (deleteMode) {
            deleteMessage.classList.remove("hidden");
            confirmButton.classList.remove("hidden");

            studentCards.forEach(card => card.classList.add("selectable"));
            studentLinks.forEach(link => link.classList.add("disabled-link")); // Disable profile click
        } else {
            deleteMessage.classList.add("hidden");
            confirmButton.classList.add("hidden");

            studentCards.forEach(card => {
                card.classList.remove("selectable", "selected");
            });
            studentLinks.forEach(link => link.classList.remove("disabled-link")); // Enable profile click

            selectedStudents.clear(); // Clear any selected students
        }
    });

    // Handle selecting student cards
    studentCards.forEach(card => {
        card.addEventListener("click", (event) => {
            if (deleteMode) {
                event.preventDefault(); // Prevent profile redirection in delete mode
                card.classList.toggle("selected");
                const studentId = card.getAttribute("data-id");

                if (card.classList.contains("selected")) {
                    selectedStudents.add(studentId);
                } else {
                    selectedStudents.delete(studentId);
                }
            }
        });
    });

    // Handle confirm button click
    confirmButton.addEventListener("click", () => {
        if (selectedStudents.size > 0) {
            fetch("/delete_student", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ student_ids: Array.from(selectedStudents) }),
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        window.location.reload(); // Reload the page after deletion
                    } else {
                        alert("Failed to delete students");
                    }
                })
                .catch(() => alert("An error occurred while deleting students."));
        } else {
            alert("No students selected for deletion.");
        }
    });
});


// phone number and email validation
document.addEventListener("DOMContentLoaded", () => {
    const phoneInput = document.getElementById("phone_number");
    const emailInput = document.getElementById("email");
    const phoneError = document.getElementById("phoneError");
    const emailError = document.getElementById("emailError");
    const saveButton = document.getElementById("saveButton");

    const validatePhoneNumber = () => {
        const phoneNumber = phoneInput.value.trim();
        const phoneRegex = /^[0-9]{10,12}$/;
        if (!phoneRegex.test(phoneNumber)) {
            phoneError.textContent = "Please enter valid phone number.";
            phoneInput.setCustomValidity("Invalid phone number");
            return false;
        } else {
            phoneError.textContent = "";
            phoneInput.setCustomValidity("");
            return true;
        }
    };

    const validateEmail = () => {
        const email = emailInput.value.trim();
        const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        if (!emailRegex.test(email)) {
            emailError.textContent = "Please enter a valid email address.";
            emailInput.setCustomValidity("Invalid email address");
            return false;
        } else {
            emailError.textContent = "";
            emailInput.setCustomValidity("");
            return true;
        }
    };

    const validateForm = () => {
        const isPhoneValid = validatePhoneNumber();
        const isEmailValid = validateEmail();
        saveButton.disabled = !(isPhoneValid && isEmailValid);
    };

    phoneInput.addEventListener("input", validatePhoneNumber);
    emailInput.addEventListener("input", validateEmail);
    document.getElementById("registerForm").addEventListener("input", validateForm);

    // Initial validation on page load
    validateForm();
});


//Date Validation

document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector("form");
    const dobInput = document.getElementById("date_of_birth");
  
    form.addEventListener("submit", function (e) {
      const dob = new Date(dobInput.value);
      const year = dob.getFullYear();
  
      if (year !== 2021) {
        e.preventDefault();
        alert("Only students born in 2021 can be registered.");
        dobInput.value = ""; // Optional: clear invalid input
      }
    });
  });
  
// table view 
document.getElementById("list-view").addEventListener("click", () => {
    const cardView = document.getElementById("card-view");
    const table = document.querySelector("table");

    // Toggle the "hidden" class for both elements
    cardView.classList.toggle("hidden");
    table.classList.toggle("hidden");
});

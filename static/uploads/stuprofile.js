document.addEventListener("DOMContentLoaded", function () {
    const ctx = document.getElementById("progressChart").getContext("2d");
    
    const progressData = {
        labels: ["Languages", "Numbers", "Creativity", "Islamic Skills", "Motor Skills", "Behavioral Skills"],
        datasets: [{
            label: "Student Progress",
            data: [6, 4, 7, 5, 2, 6], // Sample data, replace with dynamic values
            backgroundColor: "rgba(255, 99, 132, 0.5)",
            borderColor: "rgba(255, 99, 132, 1)",
            borderWidth: 1
        }]
    };

    new Chart(ctx, {
        type: "bar",
        data: progressData,
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 10
                }
            }
        }
    });
});

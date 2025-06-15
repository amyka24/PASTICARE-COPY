document.addEventListener("DOMContentLoaded", function () {
    const studentId = window.location.pathname.split("/")[2];

    fetch(`/student/${studentId}/progress_summary_data`)
        .then(res => res.json())
        .then(data => {
            const categories = [...new Set(data.map(item => item.category))]; // unique categories
            const subcatSet = new Set(data.map(item => item.subcategory));
            const subcategories = Array.from(subcatSet);

            const colors = ['#e74c3c', '#f1c40f', '#2ecc71', '#3498db', '#9b59b6', '#e67e22', '#1abc9c'];
            const datasets = subcategories.map((sub, i) => {
                const values = categories.map(cat => {
                    const match = data.find(d => d.category === cat && d.subcategory === sub);
                    return match ? match.percentage : 0;
                });

                return {
                    label: sub,
                    data: values,
                    backgroundColor: colors[i % colors.length]
                };
            });

            const ctx = document.getElementById("progressChart").getContext("2d");

            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: categories,
                    datasets: datasets
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { position: 'bottom' },
                        title: {
                            display: true,
                            text: 'Milestone Completion by Category and Subcategory'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            title: {
                                display: true,
                                text: 'Completion (%)'
                            }
                        }
                    }
                }
            });
        });
});

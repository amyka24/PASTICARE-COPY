function selectReport(value) {
    const cards = document.querySelectorAll('.report-card');
    cards.forEach(card => {
        card.querySelector('input[type="radio"]').checked = false;
        card.classList.remove('selected');
    });
    const selectedCard = document.querySelector(`input[value="${value}"]`).closest('.report-card');
    selectedCard.querySelector('input[type="radio"]').checked = true;
    selectedCard.classList.add('selected');

    // Toggle student select visibility
    const studentBox = document.getElementById("studentSelectSection");
    studentBox.style.display = (value === "individual") ? "block" : "none";
}


function toggleStudentSelect(show) {
    document.getElementById("studentSelectSection").style.display = show ? "block" : "none";
}

function showOptions(type) {
    const studentSection = document.getElementById('studentSelectSection');
    if (type === 'individual') {
        studentSection.style.display = 'block';
    } else {
        studentSection.style.display = 'none';
    }
}

function generateReport() {
    const selectedType = document.querySelector('input[name="report_type"]:checked').value;

    if (selectedType === 'individual') {
        const studentId = document.getElementById('studentSelect').value;
        if (!studentId) {
            alert("Please select a student.");
            return;
        }
        window.location.href = `/generate_report/individual/${studentId}`;
    } else if (selectedType === 'class') {
        window.location.href = `/generate_report/class`;
    } else if (selectedType === 'summary') {
        window.location.href = `/generate_report/summary`;
    } else if (selectedType === 'milestone') {
        window.location.href = `/generate_report/milestone_progress`;
    }
    else if (selectedType === 'insights') {
    window.location.href = `/generate_report/student_insights`;
}
}

function printAllCategories() {
    const chartArea = document.getElementById("chartArea");
    chartArea.innerHTML = '';

    fetch('/generate_report/summary/data/all')
        .then(res => res.json())
        .then(data => {
            let totalCharts = 0;
            let chartsRendered = 0;
            let hasPrinted = false;  // ✅ Move this OUTSIDE

            data.forEach((block, index) => {
                const categoryTitle = document.createElement('h2');
                categoryTitle.innerText = block.category;
                chartArea.appendChild(categoryTitle);

                block.subcategories.forEach((subcategory, subIndex) => {
                    const subcatTitle = document.createElement('h3');
                    subcatTitle.innerText = subcategory.subcategory;
                    chartArea.appendChild(subcatTitle);

                    const canvas = document.createElement('canvas');
                    canvas.id = `chart_${index}_${subIndex}`;
                    canvas.style.marginBottom = '20px';
                    chartArea.appendChild(canvas);

                    const labels = subcategory.milestones.map(m => m.milestone);
                    const weak = subcategory.milestones.map(m => m.counts.Weak || 0);
                    const good = subcategory.milestones.map(m => m.counts.Good || 0);
                    const excellent = subcategory.milestones.map(m => m.counts.Excellent || 0);

                    totalCharts++;

                    new Chart(canvas, {
                        type: 'bar',
                        data: {
                            labels: labels,
                            datasets: [
                                { label: 'Weak', data: weak, backgroundColor: '#e74c3c' },
                                { label: 'Good', data: good, backgroundColor: '#f1c40f' },
                                { label: 'Excellent', data: excellent, backgroundColor: '#2ecc71' }
                            ]
                        },
                        options: {
                            responsive: true,
                            plugins: {
                                title: {
                                    display: true,
                                    text: `Milestone Progress for ${subcategory.subcategory}`
                                },
                                legend: { position: 'bottom' }
                            },
                            scales: {
                                x: { stacked: true },
                                y: {
                                    stacked: true,
                                    beginAtZero: true,
                                    max: Math.max(...weak.concat(good, excellent)) + 1
                                }
                            },
                            animation: {
                                onComplete: () => {
                                    chartsRendered++;
                                    if (chartsRendered === totalCharts && !hasPrinted) {
                                        hasPrinted = true;
                                        setTimeout(() => window.print(), 500);
                                    }
                                }
                            }
                        }
                    });

                    const total = subcategory.total_milestones || 0;
                    const assessed = subcategory.assessed_count || 0;
                    const percent = total > 0 ? Math.round((assessed / total) * 100) : 0;

                    const progressWrapper = document.createElement('div');
                    progressWrapper.classList.add('progress-wrapper');
                    progressWrapper.innerHTML = `
                        <div class="progress-label">Milestone Coverage: ${assessed}/${total} (${percent}%)</div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${percent}%"></div>
                        </div>
                    `;

                    chartArea.appendChild(progressWrapper);
                });
            });
        });
}


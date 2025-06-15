function filterSubcategories() {
    const selectedCat = document.getElementById("categorySelect").value;
    const subOptions = document.querySelectorAll("#subcategorySelect option");
    const subPillsContainer = document.getElementById("subcategoryPills");
    
    // Reset and hide all
    subOptions.forEach(opt => {
        if (!opt.value) return;
        opt.style.display = opt.dataset.category === selectedCat ? "block" : "none";
    });
    
    document.getElementById("subcategorySelect").value = "";
    document.getElementById("milestoneList").innerHTML = `
        <div class="empty-state">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z"/>
            </svg>
            <p>Please select a subcategory to view milestones</p>
        </div>
    `;
    
    // Update pills
    subPillsContainer.innerHTML = '';
    subOptions.forEach(opt => {
        if (opt.value && opt.dataset.category === selectedCat) {
            const pill = document.createElement('div');
            pill.className = 'subcategory-pill';
            pill.textContent = opt.textContent;
            pill.onclick = () => {
                document.getElementById("subcategorySelect").value = opt.value;
                showMilestones();
            };
            subPillsContainer.appendChild(pill);
        }
    });
    
    
    // Update active states
    document.querySelectorAll('.selection-card').forEach((card, index) => {
        card.classList.toggle('active', index <= (selectedCat ? 1 : 0));
    });
}

function showMilestones() {
    const subcategoryId = document.getElementById("subcategorySelect").value;
    if (!subcategoryId) return;
    
    fetch(`/get_milestones/${subcategoryId}`)
        .then(res => res.json())
        .then(data => {
            const milestoneList = document.getElementById("milestoneList");
            
            if (data.length === 0) {
                milestoneList.innerHTML = `
                    <div class="empty-state">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z"/>
                        </svg>
                        <p>No milestones found for this subcategory</p>
                    </div>
                `;
                return;
            }
            
            milestoneList.innerHTML = '';
            data.forEach(item => {
                const card = document.createElement('a');
                card.className = 'milestone-card';
                card.href = `/track_progress/milestone/${item.id}`;
                card.innerHTML = `
                    <h4>${item.description}</h4>
                    <div class="progress-indicator">
                        <span class="indicator-dot"></span>
                    </div>
                `;
                milestoneList.appendChild(card);
            });
            
            // Activate the milestone step
            document.getElementById("milestoneListCard").classList.add('active');
        });
}

// Initialize search functionality
document.getElementById("milestoneSearch").addEventListener('input', function(e) {
    const searchTerm = e.target.value.toLowerCase();
    // You would implement search logic here
});

// Add this to your trackprogress.js file
function applyToAll(status) {
    // Get all radio buttons for the specified status
    const radioButtons = document.querySelectorAll(`input[type="radio"][value="${status}"]`);
    
    // Check each radio button and trigger visual feedback
    radioButtons.forEach(radio => {
        radio.checked = true;
        
        // Find the corresponding visual indicator
        const visual = radio.nextElementSibling;
        if (visual) {
            // Add animation effect
            visual.style.transform = 'scale(1.2)';
            setTimeout(() => {
                visual.style.transform = 'scale(1.1)';
            }, 200);
        }
    });
}

// Add click animation for radio buttons
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.radio-visual').forEach(visual => {
        visual.addEventListener('click', function() {
            this.style.transform = 'scale(1.2)';
            setTimeout(() => {
                this.style.transform = 'scale(1.1)';
            }, 200);
        });
    });
});

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.bar-segment').forEach(bar => {
        const width = bar.getAttribute('data-width');
        if (width) {
            bar.style.width = `${width}%`;
        }
    });
});

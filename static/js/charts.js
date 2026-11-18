// Wait until DOM is fully loaded
document.addEventListener('DOMContentLoaded', function () {
    if (!window.dashboardData) {
        return;
    }

    const data = window.dashboardData;

    // ----------------------------------------------------
    // 1. Topic-wise Solved Problems Chart (Chart.js)
    // ----------------------------------------------------
    const topicCtx = document.getElementById('topicBarChart');
    if (topicCtx) {
        // Highlight weak topics in amber, others in clean blue
        const barColors = data.topicLabels.map(tag => {
            if (data.weakTopics && data.weakTopics.includes(tag.toLowerCase())) {
                return '#d97706'; // Amber for weak topics
            }
            return '#2563eb'; // Royal blue for regular topics
        });

        new Chart(topicCtx, {
            type: 'bar',
            data: {
                labels: data.topicLabels,
                datasets: [{
                    label: 'Solved Problems',
                    data: data.topicCounts,
                    backgroundColor: barColors,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            afterLabel: function (context) {
                                const tag = context.label.toLowerCase();
                                if (data.weakTopics && data.weakTopics.includes(tag)) {
                                    return '⚠️ One of your weakest topics!';
                                }
                                return '';
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#475569', font: { family: "'Plus Jakarta Sans', sans-serif" } },
                        grid: { color: '#f1f5f9' }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: { color: '#475569', precision: 0, font: { family: "'Plus Jakarta Sans', sans-serif" } },
                        grid: { color: '#f1f5f9' }
                    }
                }
            }
        });
    }

    // ----------------------------------------------------
    // 2. Rating Range Distribution Chart (Chart.js)
    // ----------------------------------------------------
    const ratingCtx = document.getElementById('ratingDistChart');
    if (ratingCtx) {
        new Chart(ratingCtx, {
            type: 'bar',
            data: {
                labels: data.ratingLabels,
                datasets: [{
                    label: 'Problems Count',
                    data: data.ratingCounts,
                    backgroundColor: '#6366f1',
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#475569', font: { family: "'Plus Jakarta Sans', sans-serif" } },
                        grid: { color: '#f1f5f9' }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: { color: '#475569', precision: 0, font: { family: "'Plus Jakarta Sans', sans-serif" } },
                        grid: { color: '#f1f5f9' }
                    }
                }
            }
        });
    }

    // ----------------------------------------------------
    // 3. Shuffle Problems Button via AJAX / fetch
    // ----------------------------------------------------
    const shuffleBtn = document.getElementById('shuffleBtn');
    const problemsGrid = document.getElementById('problemsGrid');

    if (shuffleBtn && problemsGrid) {
        shuffleBtn.addEventListener('click', function () {
            // Animate button state
            shuffleBtn.disabled = true;
            shuffleBtn.innerHTML = '<span class="shuffle-icon">⏳</span> Shuffling...';

            // Build query params
            const params = new URLSearchParams();
            if (data.typicalRating) {
                params.append('typical_rating', data.typicalRating);
            }
            if (data.weakTopics) {
                data.weakTopics.forEach(t => params.append('weak_topics', t));
            }

            fetch(`/api/recommendations/shuffle?${params.toString()}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network error during shuffle');
                    }
                    return response.json();
                })
                .then(res => {
                    if (res.status === 'success' && res.problems) {
                        renderProblems(res.problems, data.weakTopics);
                    }
                })
                .catch(err => {
                    console.error('Shuffle error:', err);
                    alert('Could not shuffle problems. Please try again.');
                })
                .finally(() => {
                    shuffleBtn.disabled = false;
                    shuffleBtn.innerHTML = '<span class="shuffle-icon">🎲</span> <span>Shuffle Problems</span>';
                });
        });
    }

    /**
     * Renders recommended problem cards into the DOM
     */
    function renderProblems(problems, weakTopics) {
        problemsGrid.innerHTML = '';

        if (!problems || problems.length === 0) {
            problemsGrid.innerHTML = '<p class="text-secondary">No problems available in candidate pool.</p>';
            return;
        }

        const normalizedWeak = (weakTopics || []).map(w => w.toLowerCase());

        problems.forEach(prob => {
            const card = document.createElement('div');
            card.className = 'card problem-card';

            // Build tags HTML
            let tagsHtml = '';
            if (prob.tags && prob.tags.length > 0) {
                prob.tags.forEach(tag => {
                    const isWeak = normalizedWeak.includes(tag.toLowerCase());
                    tagsHtml += `<span class="tag-pill ${isWeak ? 'tag-weak' : ''}">${tag}</span>`;
                });
            }

            card.innerHTML = `
                <div class="problem-card-top">
                    <span class="problem-code">${prob.contestId}${prob.index}</span>
                    <span class="badge badge-rating">Rating: ${prob.rating}</span>
                </div>
                <h4 class="problem-name">${prob.name}</h4>
                <div class="problem-tags">
                    ${tagsHtml}
                </div>
                <div class="problem-action">
                    <a href="${prob.link}" target="_blank" class="btn btn-sm btn-solve">
                        Solve on Codeforces ↗
                    </a>
                </div>
            `;

            problemsGrid.appendChild(card);
        });
    }
});

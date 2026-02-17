// LegoWorld V3 - Tizen TV Application
// Main JavaScript for scene navigation and photo gallery

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const bgImage = document.getElementById('bg-image');
    const dashboard = document.getElementById('dashboard');
    const sceneTitle = document.getElementById('scene-title');
    const videoPlayerView = document.getElementById('video-player');
    const videoElement = document.getElementById('main-video');
    const videoSource = document.getElementById('video-source');
    const myPhotosView = document.getElementById('my-photos-view');
    const photoGrid = document.getElementById('photo-grid');
    const newPhotoIndicator = document.getElementById('new-photo-indicator');
    const fullscreenPhoto = document.getElementById('fullscreen-photo');
    const fullscreenImg = document.getElementById('fullscreen-img');
    const fullscreenCaption = document.getElementById('fullscreen-caption');

    // State
    let currentScene = 'SmartBrick1';
    let currentView = 'dashboard'; // 'dashboard', 'video', 'photos', 'fullscreen'
    let photos = [];
    let lastPhotoCount = 0;
    let focusedPhotoIndex = 0;

    // Backend URL - ngrok tunnel for mobile sync
    const BACKEND_URL = 'https://marlena-glossological-hyperconfidently.ngrok-free.dev';

    // Scene Configuration (from V2, keeping existing scenes)
    const sceneAssets = {
        'SmartBrick1': { img: 'assets/smartbrick1.jpg', video: null, title: 'SmartBrick' },
        'SmartBrick2': { img: 'assets/smartbrick2.jpg', video: null, title: 'SmartBrick 2' },
        'City': { img: 'assets/city1.jpg', video: 'assets/city.mp4', title: 'City' },
        'Firetruck': { img: 'assets/firetruck.jpg', video: 'assets/firetruck.mp4', title: 'Fire Truck' },
        'Universe': { img: 'assets/Lego universe.jpg', video: 'assets/Lego universe starwars.mp4', title: 'Universe' },
        'Space': { img: 'assets/space.png', video: 'assets/space.mp4', title: 'Space' },
        'Game': { img: 'assets/game.png', video: null, title: 'Game' },
        'MyPhotos': { img: null, video: null, title: 'My Lego' } // New scene
    };

    // Navigation order
    const sceneOrder = ['SmartBrick1', 'SmartBrick2', 'City', 'Firetruck', 'Universe', 'Space', 'Game', 'MyPhotos'];
    let sceneIndex = 0;

    // Initialize
    updateScene(sceneOrder[0]);
    startPolling();

    // Scene Navigation
    function updateScene(sceneName) {
        console.log(`Switching to scene: ${sceneName}`);
        currentScene = sceneName;

        if (sceneName === 'MyPhotos') {
            // Show photo gallery
            showPhotoGallery();
        } else {
            // Show regular scene
            const scene = sceneAssets[sceneName];
            if (scene.img) {
                bgImage.src = scene.img;
            }
            sceneTitle.textContent = scene.title;
        }
    }

    function navigateUp() {
        // Allow navigation from dashboard or photo gallery
        if (currentView === 'dashboard' || currentView === 'photos') {
            if (currentView === 'photos') {
                hidePhotoGallery();
            }
            sceneIndex = (sceneIndex - 1 + sceneOrder.length) % sceneOrder.length;
            updateScene(sceneOrder[sceneIndex]);
        }
    }

    function navigateDown() {
        // Allow navigation from dashboard or photo gallery
        if (currentView === 'dashboard' || currentView === 'photos') {
            if (currentView === 'photos') {
                hidePhotoGallery();
            }
            sceneIndex = (sceneIndex + 1) % sceneOrder.length;
            updateScene(sceneOrder[sceneIndex]);
        }
    }

    function handleEnter() {
        if (currentView === 'dashboard') {
            const scene = sceneAssets[currentScene];
            if (scene.video) {
                playVideo();
            } else if (currentScene === 'MyPhotos') {
                showPhotoGallery();
            }
        } else if (currentView === 'photos') {
            // Refresh photos to sync with mobile uploads
            console.log('🔄 Refreshing photos...');
            loadPhotos();
        }
    }

    function handleBack() {
        if (currentView === 'video') {
            stopVideo();
        } else if (currentView === 'photos') {
            hidePhotoGallery();
        } else if (currentView === 'fullscreen') {
            hideFullscreenPhoto();
        }
    }

    // Video Playback
    function playVideo() {
        const scene = sceneAssets[currentScene];
        if (!scene.video) return;

        console.log(`Playing video: ${scene.video}`);
        videoSource.src = scene.video;
        videoElement.load();

        dashboard.classList.add('hidden');
        dashboard.classList.remove('active');

        videoPlayerView.classList.add('active');
        videoPlayerView.classList.remove('hidden');

        currentView = 'video';

        videoElement.play().catch(e => console.error("Play error:", e));
        videoElement.onended = stopVideo;
    }

    function stopVideo() {
        console.log("Stopping video");
        videoElement.pause();
        videoSource.src = "";

        videoPlayerView.classList.add('hidden');
        videoPlayerView.classList.remove('active');

        dashboard.classList.add('active');
        dashboard.classList.remove('hidden');

        currentView = 'dashboard';
    }

    // Photo Gallery
    async function loadPhotos() {
        try {
            const response = await fetch(`${BACKEND_URL}/api/photos`, {
                headers: {
                    'ngrok-skip-browser-warning': 'true'
                }
            });
            if (response.ok) {
                const data = await response.json();

                // Check if new photos were added
                if (data.length > lastPhotoCount) {
                    console.log("New photos detected!");
                    showNewPhotoIndicator();
                }

                lastPhotoCount = data.length;
                photos = data;
                renderPhotoGrid();
            }
        } catch (error) {
            console.error("Error loading photos:", error);
        }
    }

    function renderPhotoGrid() {
        photoGrid.innerHTML = '';

        if (photos.length === 0) {
            photoGrid.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; padding: 100px; color: #2C2C2C;">
                    <h2 style="font-size: 48px; margin-bottom: 20px;">No photos yet!</h2>
                    <p style="font-size: 32px;">Add photos from your mobile app</p>
                </div>
            `;
            return;
        }

        photos.forEach((photo, index) => {
            const card = document.createElement('div');
            card.className = 'photo-card';

            // Check if photo is new (less than 1 hour old)
            const timeAgo = Date.now() / 1000 - photo.created_at;
            const isNew = timeAgo < 3600; // 1 hour

            if (isNew) {
                card.classList.add('new');
            }

            // Focus first photo by default
            if (index === focusedPhotoIndex) {
                card.classList.add('focused');
            }

            // Format time
            let timeStr;
            if (timeAgo < 60) {
                timeStr = 'Just now';
            } else if (timeAgo < 3600) {
                timeStr = `${Math.floor(timeAgo / 60)}m ago`;
            } else if (timeAgo < 86400) {
                timeStr = `${Math.floor(timeAgo / 3600)}h ago`;
            } else {
                timeStr = `${Math.floor(timeAgo / 86400)}d ago`;
            }

            card.innerHTML = `
                <img src="${BACKEND_URL}/api/photos/${photo.filename}" alt="Lego Photo">
                <div class="photo-info">
                    <div class="photo-caption">${photo.caption || 'My Lego Set'}</div>
                    <div class="photo-time">
                        <span>${timeStr}</span>
                        ${isNew ? '<span class="new-badge">NEW</span>' : ''}
                    </div>
                </div>
            `;

            photoGrid.appendChild(card);
        });
    }

    function showPhotoGallery() {
        console.log("Showing photo gallery");

        dashboard.classList.add('hidden');
        dashboard.classList.remove('active');

        myPhotosView.classList.add('active');
        myPhotosView.classList.remove('hidden');

        currentView = 'photos';
        focusedPhotoIndex = 0;

        loadPhotos();
    }

    function hidePhotoGallery() {
        if (currentView !== 'photos') return; // Already hidden

        console.log("Hiding photo gallery");

        myPhotosView.classList.add('hidden');
        myPhotosView.classList.remove('active');

        dashboard.classList.add('active');
        dashboard.classList.remove('hidden');

        currentView = 'dashboard';
    }

    function showNewPhotoIndicator() {
        newPhotoIndicator.classList.remove('hidden');

        // Auto-hide after 5 seconds
        setTimeout(() => {
            newPhotoIndicator.classList.add('hidden');
        }, 5000);
    }

    function showFullscreenPhoto(photo) {
        if (!photo) return;

        console.log("Showing fullscreen photo");

        fullscreenImg.src = `${BACKEND_URL}/api/photos/${photo.filename}`;
        fullscreenCaption.textContent = photo.caption || 'My Lego Set';

        myPhotosView.classList.add('hidden');
        fullscreenPhoto.classList.add('active');
        fullscreenPhoto.classList.remove('hidden');

        currentView = 'fullscreen';
    }

    function hideFullscreenPhoto() {
        console.log("Hiding fullscreen photo");

        fullscreenPhoto.classList.add('hidden');
        fullscreenPhoto.classList.remove('active');

        myPhotosView.classList.add('active');
        myPhotosView.classList.remove('hidden');

        currentView = 'photos';
    }

    // Polling for new photos
    function startPolling() {
        setInterval(async () => {
            try {
                const response = await fetch(`${BACKEND_URL}/api/state`, {
                    headers: {
                        'ngrok-skip-browser-warning': 'true'
                    }
                });
                if (response.ok) {
                    const state = await response.json();

                    // Update photo count and reload if needed
                    if (state.total_count > lastPhotoCount && currentView === 'photos') {
                        loadPhotos();
                    } else if (state.total_count > lastPhotoCount) {
                        // Just update the count, will load when user navigates to photos
                        lastPhotoCount = state.total_count;
                    }
                }
            } catch (error) {
                console.error("Polling error:", error);
            }
        }, 2000); // Poll every 2 seconds
    }

    // Remote Control Event Handler
    document.addEventListener('keydown', (e) => {
        console.log('Key pressed:', e.keyCode);

        switch (e.keyCode) {
            case 38: // UP Arrow
                navigateUp();
                break;

            case 40: // DOWN Arrow
                navigateDown();
                break;

            case 13: // ENTER
                handleEnter();
                break;

            case 10009: // RETURN / BACK (Tizen)
            case 27:    // ESC (Desktop)
                handleBack();
                break;

            case 37: // LEFT Arrow (for photo navigation in future)
                if (currentView === 'photos' && focusedPhotoIndex > 0) {
                    focusedPhotoIndex--;
                    renderPhotoGrid();
                }
                break;

            case 39: // RIGHT Arrow (for photo navigation in future)
                if (currentView === 'photos' && focusedPhotoIndex < photos.length - 1) {
                    focusedPhotoIndex++;
                    renderPhotoGrid();
                }
                break;
        }
    });
});

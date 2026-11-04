/* Weather & Agro-Climatic Advisory Controller (Live Location & Force Refresh Enhanced) */

const WeatherController = {
    currentLat: 12.9716,
    currentLon: 77.5946,
    currentCity: "Bengaluru Rural",
    isLiveGps: false,

    init() {
        console.log('[WeatherController] Initializing live weather & spray advisory...');
        const refreshBtn = document.getElementById('refresh-weather-btn');
        if (refreshBtn) refreshBtn.addEventListener('click', () => this.fetchWeather(true));

        const liveGpsBtn = document.getElementById('weather-live-gps-btn');
        if (liveGpsBtn) liveGpsBtn.addEventListener('click', () => this.useLiveLocation());

        this.fetchWeather();
    },

    useLiveLocation() {
        if (!navigator.geolocation) {
            Components.showToast('Geolocation is not supported by your browser.', 'warning');
            return;
        }

        Components.showToast('📍 Acquiring live GPS position for weather forecast...', 'info');
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                this.currentLat = Number(pos.coords.latitude.toFixed(4));
                this.currentLon = Number(pos.coords.longitude.toFixed(4));
                this.currentCity = `My Farm (${this.currentLat}°N, ${this.currentLon}°E)`;
                this.isLiveGps = true;

                const liveBtn = document.getElementById('weather-live-gps-btn');
                if (liveBtn) {
                    liveBtn.classList.add('btn-success');
                    liveBtn.classList.remove('btn-outline');
                    liveBtn.innerHTML = `📍 Live GPS Active (${this.currentLat}°, ${this.currentLon}°)`;
                }

                Components.showToast(`🎯 Weather localized to: ${this.currentLat}°N, ${this.currentLon}°E (±${Math.round(pos.coords.accuracy)}m)`, 'success');
                this.fetchWeatherForLocation(this.currentLat, this.currentLon, this.currentCity, true);
            },
            (err) => {
                console.warn('[WeatherController] GPS position error:', err);
                Components.showToast('Could not acquire precise GPS. Showing regional Bengaluru Rural weather.', 'warning');
                this.fetchWeather(true);
            },
            { enableHighAccuracy: true, timeout: 8000 }
        );
    },

    async fetchWeather(force = false) {
        return this.fetchWeatherForLocation(this.currentLat, this.currentLon, this.currentCity, force);
    },

    async fetchWeatherForLocation(lat, lon, cityName, force = false) {
        try {
            this.currentLat = lat;
            this.currentLon = lon;
            this.currentCity = cityName;

            const refreshBtn = document.getElementById('refresh-weather-btn');
            if (refreshBtn && force) {
                refreshBtn.disabled = true;
                refreshBtn.innerHTML = '⏳ Syncing...';
            }

            const url = `/api/weather?lat=${lat}&lon=${lon}&city=${encodeURIComponent(cityName)}&refresh=${force ? 'true' : 'false'}`;
            const res = await fetch(url);
            const data = await res.json();
            this.renderWeather(data);

            if (refreshBtn) {
                refreshBtn.disabled = false;
                refreshBtn.innerHTML = '🔄 Refresh Weather';
            }

            if (force) {
                Components.showToast(`✅ Live weather updated for ${cityName}`, 'success');
            }
        } catch (err) {
            console.error('[WeatherController] Weather fetch error:', err);
            const refreshBtn = document.getElementById('refresh-weather-btn');
            if (refreshBtn) {
                refreshBtn.disabled = false;
                refreshBtn.innerHTML = '🔄 Refresh Weather';
            }
        }
    },

    renderWeather(data) {
        if (!data || !data.current) return;

        // Current weather elements
        const tempEl = document.getElementById('weather-temp');
        const feelsEl = document.getElementById('weather-feels');
        const descEl = document.getElementById('weather-desc');
        const humidityEl = document.getElementById('weather-humidity');
        const windEl = document.getElementById('weather-wind');
        const rainEl = document.getElementById('weather-rain');
        const cityEl = document.getElementById('weather-city');
        const updatedEl = document.getElementById('weather-updated-time');

        if (tempEl) tempEl.textContent = `${data.current.temperature}°C`;
        if (feelsEl) feelsEl.textContent = `Feels like ${data.current.apparent_temperature}°C`;
        if (descEl) descEl.textContent = data.current.weather_desc;
        if (humidityEl) humidityEl.textContent = `${data.current.humidity}%`;
        if (windEl) windEl.textContent = `${data.current.wind_speed} km/h`;
        if (rainEl) rainEl.textContent = `${data.current.precipitation || 0} mm`;
        if (cityEl) cityEl.textContent = data.city || this.currentCity;
        if (updatedEl) updatedEl.textContent = `Updated: ${data.updated_at || 'Just now'}`;

        // Spraying advisory condition
        const sprayConditionEl = document.getElementById('weather-spray-condition');
        const sprayReasonEl = document.getElementById('weather-spray-reason');
        const sprayActionEl = document.getElementById('weather-spray-action');

        if (data.agri_advisory) {
            const adv = data.agri_advisory;
            if (sprayConditionEl) {
                sprayConditionEl.textContent = adv.spray_condition;
                sprayConditionEl.className = `badge badge-${adv.spray_color || 'info'}`;
            }
            if (sprayReasonEl) sprayReasonEl.textContent = adv.spray_reason;
            if (sprayActionEl) sprayActionEl.textContent = adv.action;
        }

        // Render 24-hr spray hours
        const sprayHoursContainer = document.getElementById('weather-hourly-spray');
        if (sprayHoursContainer && data.spray_hours_next_24) {
            sprayHoursContainer.innerHTML = data.spray_hours_next_24.map(h => `
                <div style="flex: 0 0 85px; text-align: center; padding: 10px 8px; border: 1px solid var(--border-color); border-radius: var(--radius-sm); background: ${h.status === 'Good' ? 'rgba(76, 175, 80, 0.08)' : (h.status === 'Fair' ? 'rgba(255, 152, 0, 0.08)' : 'rgba(244, 67, 54, 0.08)')};">
                    <div style="font-size: 11px; font-weight: 700; color: var(--text-muted);">${h.time}</div>
                    <div style="font-size: 14px; font-weight: 800; margin: 4px 0; color: var(--text-primary);">${h.temp}°</div>
                    <div style="font-size: 10px; color: var(--text-secondary); margin-bottom: 4px;">💨 ${h.wind} km/h</div>
                    <span class="badge ${h.status === 'Good' ? 'badge-healthy' : (h.status === 'Fair' ? 'badge-warning' : 'badge-danger')}" style="font-size: 9.5px; padding: 2px 5px;">
                        ${h.status}
                    </span>
                </div>
            `).join('');
        }

        // Render 7-day forecast
        const forecastContainer = document.getElementById('weather-forecast-days');
        if (forecastContainer && data.forecast_days) {
            forecastContainer.innerHTML = data.forecast_days.map(d => `
                <div class="agri-card" style="padding: 14px; text-align: center;">
                    <div style="font-size: 12px; font-weight: 700; color: var(--primary-800);">${d.day_name}</div>
                    <div style="font-size: 11px; color: var(--text-muted);">${d.date}</div>
                    <div style="font-size: 22px; margin: 8px 0;">🌤️</div>
                    <div style="font-size: 14px; font-weight: 800; color: var(--text-primary);">${d.max_temp}° / ${d.min_temp}°</div>
                    <div style="font-size: 11px; color: var(--text-secondary); margin: 4px 0;">${d.weather_desc}</div>
                    <span class="badge ${d.spray_suitability === 'Good' ? 'badge-healthy' : 'badge-warning'}" style="font-size: 10px;">
                        ${d.spray_suitability === 'Good' ? 'Spray: Optimal' : 'Spray: Caution'}
                    </span>
                </div>
            `).join('');
        }
    }
};

window.WeatherController = WeatherController;

// API Client helper functions for AJAX requests

const API = {
    async request(url, options = {}) {
        const defaultHeaders = {};
        if (!(options.body instanceof FormData)) {
            defaultHeaders['Content-Type'] = 'application/json';
        }
        
        options.headers = {
            ...defaultHeaders,
            ...options.headers
        };
        
        // If data is passed as object, serialize to JSON (except FormData)
        if (options.body && !(options.body instanceof FormData) && typeof options.body === 'object') {
            options.body = JSON.stringify(options.body);
        }

        try {
            const response = await fetch(url, options);
            const data = await response.json();
            
            if (!response.ok) {
                return { 
                    error: data.error || `HTTP error! Status: ${response.status}`, 
                    status: response.status 
                };
            }
            
            return { data, status: response.status };
        } catch (error) {
            console.error('API Request Error:', error);
            return { error: 'Connection failed. Please check your network connection.' };
        }
    },

    // Authentication endpoints
    async login(email, password) {
        return this.request('/api/auth/login', {
            method: 'POST',
            body: { email, password }
        });
    },

    async register(email, password, role = 'candidate') {
        return this.request('/api/auth/register', {
            method: 'POST',
            body: { email, password, role }
        });
    },

    async logout() {
        return this.request('/api/auth/logout', { method: 'POST' });
    },

    async checkSession() {
        return this.request('/api/auth/session');
    },

    // Candidate profile endpoints
    async getProfile() {
        return this.request('/api/candidate/profile');
    },

    async updateProfile(profileData) {
        return this.request('/api/candidate/profile', {
            method: 'POST',
            body: profileData
        });
    },

    async uploadResume(formData) {
        // Omit Content-Type header so the browser sets the boundary for multipart/form-data
        return this.request('/api/candidate/profile/upload-resume', {
            method: 'POST',
            headers: {},
            body: formData
        });
    },

    // Recommendation and listings
    async getRecommendations() {
        return this.request('/api/candidate/recommendations');
    },

    async getRecommendationHistory() {
        return this.request('/api/candidate/recommendations/history');
    },

    async getRoadmap(internshipId) {
        return this.request(`/api/candidate/recommendations/${internshipId}/roadmap`);
    },

    async getInternships(params = {}) {
        const queryStr = new URLSearchParams(params).toString();
        return this.request(`/api/internships?${queryStr}`);
    },

    async getInternshipDetail(id) {
        return this.request(`/api/internships/${id}`);
    },

    // Bookmarking/applying
    async getSavedInternships() {
        return this.request('/api/candidate/saved');
    },

    async toggleSaveInternship(id, isSave) {
        return this.request(`/api/candidate/saved/${id}`, {
            method: isSave ? 'POST' : 'DELETE'
        });
    },

    async applyInternship(id) {
        return this.request(`/api/candidate/apply/${id}`, {
            method: 'POST'
        });
    },

    async getAppliedInternships() {
        return this.request('/api/candidate/applied');
    },

    async getCandidateInsights() {
        return this.request('/api/candidate/insights');
    },

    // Admin endpoints
    async getAdminUsers() {
        return this.request('/api/admin/users');
    },

    async getAdminStats() {
        return this.request('/api/admin/stats');
    },

    async addInternship(internshipData) {
        return this.request('/api/admin/internships', {
            method: 'POST',
            body: internshipData
        });
    },

    async updateInternship(id, internshipData) {
        return this.request(`/api/admin/internships/${id}`, {
            method: 'PUT',
            body: internshipData
        });
    },

    async deleteInternship(id) {
        return this.request(`/api/admin/internships/${id}`, {
            method: 'DELETE'
        });
    }
};

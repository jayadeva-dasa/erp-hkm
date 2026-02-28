import apiClient from './apiClient';

// Use HKM wrapper APIs with permission checks
export const DONATION_INSIGHTS_ENDPOINT =
  '/api/method/hkm.api.hkm_dashboard.donation_insights.get_donation_insights';

export const DONOR_SEARCH_ENDPOINT =
  '/api/method/hkm.api.hkm_dashboard.donor_search.search_donors';

export const fetchDonationInsights = (params = {}, signal) =>
  apiClient.get(DONATION_INSIGHTS_ENDPOINT, {
    params,
    signal,
  });

export const searchDonors = (params = {}, signal) =>
  apiClient.get(DONOR_SEARCH_ENDPOINT, {
    params,
    signal,
  });


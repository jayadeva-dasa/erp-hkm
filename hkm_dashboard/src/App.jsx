import React, { Suspense, lazy } from 'react';
import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Box } from '@chakra-ui/react';
import HomePage from './pages/HomePage';
import FullPageLoader from './components/shared/FullPageLoader';

const DonationInsightsPage = lazy(() => import('./modules/donation-insights/pages/DonationInsightsPage'));
const DonorSearchPage = lazy(() => import('./modules/donor-search/pages/DonorSearchPage'));
const EagleViewPage = lazy(() => import('./modules/eagle-view/pages/EagleViewPage'));
const AssetRecoPage = lazy(() => import('./modules/asset_reco/pages/AssetRecoPage'));
const HKMPayUserManagementPage = lazy(() => import('./modules/hkm_pay_user_management/pages/HKMPayUserManagementPage'));
const UserEntriesPage = lazy(() => import('./modules/hkm_pay_user_management/pages/UserEntriesPage'));
const AssetDashboardPage = lazy(() => import('./modules/asset_management/pages/AssetDashboardPage'));
const AssetListPage = lazy(() => import('./modules/asset_management/pages/AssetListPage'));
const CreateAssetPage = lazy(() => import('./modules/asset_management/pages/CreateAssetPage'));
const AssetMovementPage = lazy(() => import('./modules/asset_management/pages/AssetMovementPage'));
const AssetMovementsHistoryPage = lazy(() => import('./modules/asset_management/pages/AssetMovementsHistoryPage'));
const AssetSpecificationsPage = lazy(() => import('./modules/asset_management/pages/AssetSpecificationsPage'));
const AssetDetailPage = lazy(() => import('./modules/asset_management/pages/AssetDetailPage'));
const ScrapAssetPage = lazy(() => import('./modules/asset_management/pages/ScrapAssetPage'));
const SellAssetPage = lazy(() => import('./modules/asset_management/pages/SellAssetPage'));
const ReportLostAssetPage = lazy(() => import('./modules/asset_management/pages/ReportLostAssetPage'));
const S3FileSearchPage = lazy(() => import('./modules/s3_file_search/pages/S3FileSearchPage'));
const GuestHouseManagementPage = lazy(() => import('./modules/guest_house/pages/GuestHouseManagementPage'));
const NewBookingPage = lazy(() => import('./modules/guest_house/pages/NewBookingPage'));
const BookingsPage = lazy(() => import('./modules/guest_house/pages/BookingsPage'));
const CategoryAnalyticsPage = lazy(() => import('./modules/category_analytics/pages/Dashboard'));
const BalanceSheetReportPage = lazy(() => import('./modules/category_analytics/pages/BalanceSheetReport'));
const PLReportPage = lazy(() => import('./modules/category_analytics/pages/PLReport'));
const DailySalesReportPage = lazy(() => import('./modules/daily_sales_report/pages/DailySalesReportPage'));
const ChartOfAccountsPage = lazy(() => import('./modules/chart_of_accounts_manager/pages/ChartOfAccountsPage'));

function App() {
  return (
    <HashRouter>
      <Box minH="100vh" bg="gray.50">
        <Suspense fallback={<FullPageLoader label="Loading module..." />}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/donation-insights" element={<DonationInsightsPage />} />
            <Route path="/donor-search" element={<DonorSearchPage />} />
            <Route path="/eagle-view" element={<EagleViewPage />} />
            <Route path="/asset-reco" element={<AssetRecoPage />} />
            <Route path="/hkm-pay-user-management" element={<HKMPayUserManagementPage />} />
            <Route path="/hkm-pay-user-management/entries/:userId" element={<UserEntriesPage />} />
            <Route path="/asset-dashboard" element={<AssetDashboardPage />} />
            <Route path="/asset-dashboard/list" element={<AssetListPage />} />
            <Route path="/asset-dashboard/create" element={<CreateAssetPage />} />
            <Route path="/asset-dashboard/move" element={<AssetMovementPage />} />
            <Route path="/asset-dashboard/movements" element={<AssetMovementsHistoryPage />} />
            <Route path="/asset-dashboard/specifications" element={<AssetSpecificationsPage />} />
            <Route path="/asset-dashboard/detail/:assetId" element={<AssetDetailPage />} />
            <Route path="/asset-dashboard/scrap" element={<ScrapAssetPage />} />
            <Route path="/asset-dashboard/sell" element={<SellAssetPage />} />
            <Route path="/asset-dashboard/lost" element={<ReportLostAssetPage />} />
            <Route path="/s3-file-search" element={<S3FileSearchPage />} />
            <Route path="/guest-house" element={<GuestHouseManagementPage />} />
            <Route path="/guest-house/new-booking" element={<NewBookingPage />} />
            <Route path="/guest-house/bookings" element={<BookingsPage />} />
            <Route path="/category-analytics" element={<CategoryAnalyticsPage />} />
            <Route path="/category-analytics/balance-sheet" element={<BalanceSheetReportPage />} />
            <Route path="/category-analytics/pl-report" element={<PLReportPage />} />
            <Route path="/daily-sales-report" element={<DailySalesReportPage />} />
            <Route path="/chart-of-accounts" element={<ChartOfAccountsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </Box>
    </HashRouter>
  );
}

export default App;


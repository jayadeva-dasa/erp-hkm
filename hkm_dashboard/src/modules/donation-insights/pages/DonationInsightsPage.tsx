import {
  Alert,
  AlertIcon,
  Badge,
  Box,
  Button,
  Checkbox,
  Flex,
  Heading,
  Input,
  Menu,
  MenuButton,
  MenuList,
  Select,
  SimpleGrid,
  Spinner,
  Stack,
  Table,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tr,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  useToast,
} from '@chakra-ui/react';
import type { ButtonProps } from '@chakra-ui/react';
import { ChevronDownIcon } from '@chakra-ui/icons';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { format, subDays } from 'date-fns';
import {
  ComposedChart,
  Line,
  Bar,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import { FiDownload } from 'react-icons/fi';
import { fetchDonationInsights } from '../../../services/dhananjayaApi';
import PageHeader from '../../../components/shared/PageHeader';

const DONATION_INSIGHTS_ENDPOINT =
  '/api/method/dhananjaya.dhananjaya.api.donation_insights.get_donation_insights';
const DONOR_SEARCH_PAGE_LENGTH = 10;

interface FiscalYearOption {
  name: string;
  label: string;
  start: string;
  end: string;
}

interface Summary {
  total_amount: number;
  total_receipts: number;
  unique_donors: number;
  unique_patrons: number;
  average_donation: number;
}

interface MonthlyTrend {
  month: string;
  label: string;
  total_amount: number;
  receipt_count: number;
  average_donation: number;
}

interface PaymentMethodRow {
  payment_method: string;
  total_amount: number;
  receipt_count: number;
  average: number;
}

interface CompanyRow {
  company: string;
  total_amount: number;
  receipt_count: number;
  average: number;
}

interface AvailableCompany {
  name: string;
  label: string;
}

interface BreakdownEntry {
  id: string | null;
  label: string;
  total_amount: number;
  receipt_count: number;
  average: number;
}

interface BreakdownSummary {
  included_amount: number;
  included_count: number;
  excluded_amount: number;
  excluded_count: number;
}

interface BreakdownResponse {
  summary: BreakdownSummary;
  included: BreakdownEntry[];
  excluded: BreakdownEntry[];
}

interface TopEntity {
  id: string;
  label: string;
  total_amount: number;
  receipt_count: number;
  average: number;
  last_receipt?: string | null;
}

interface GrowthRow {
  month: string;
  label: string;
  current_amount: number;
  previous_amount: number;
  growth_amount: number;
  growth_percentage: number;
}

interface RecentMomentum {
  overall_growth_pct?: number;
  best_month?: MonthlyTrend;
  worst_month?: MonthlyTrend;
  recent_momentum?: 'up' | 'down' | 'mixed' | 'stable';
}

interface CurrentMonthSnapshot {
  from_date: string;
  to_date: string;
  realized_amount: number;
  realized_count: number;
  acknowledged_amount: number;
  acknowledged_count: number;
  total_amount: number;
  total_count: number;
  by_payment_method: PaymentMethodRow[];
}

interface ExcludedSummary {
  total_amount: number;
  total_count: number;
  reasons: { label: string; count: number; amount: number }[];
}

interface ViewPayload {
  summary: Summary;
  monthly_trends: MonthlyTrend[];
  growth_trends: GrowthRow[];
  highlights: RecentMomentum;
  payment_methods: PaymentMethodRow[];
  companies: CompanyRow[];
  top_donors: TopEntity[];
  top_patrons: TopEntity[];
  current_month: CurrentMonthSnapshot;
  excluded: ExcludedSummary;
}

interface DonorOverviewStats {
  total_identities: number;
  total_donors: number;
  active_status: number;
  dormant_status: number;
  active_recent: number;
  donated_this_year: number;
  new_last_year: number;
  new_previous_year: number;
  growth_rate_pct: number | null;
}

interface PatronCategoryStats {
  seva_type: string | null;
  label: string | null;
  patron_count: number;
  committed_amount: number;
  donated_amount: number;
  remaining_amount: number;
  completion_pct: number | null;
  fulfilled_count: number;
}

interface PatronOverviewStats {
  total_patrons: number;
  active_recent: number;
  donated_this_year: number;
  committed_total: number;
  donated_total: number;
  remaining_total: number;
  new_last_year: number;
  new_previous_year: number;
  growth_rate_pct: number | null;
  categories: PatronCategoryStats[];
}

interface AggregateIdentityStats {
  total_identities: number;
  linked_donors: number;
  linked_patrons: number;
  average_donors_per_identity: number | null;
  fiscal_year: string;
}

interface LocationPoint {
  label: string;
  city?: string | null;
  state?: string | null;
  country?: string | null;
  latitude: number | null;
  longitude: number | null;
  address_count: number;
  identity_count: number;
}

interface LocationListEntry {
  country?: string | null;
  state?: string | null;
  identity_count: number;
}

interface LocationOverview {
  points: LocationPoint[];
  top_countries: LocationListEntry[];
  top_states: LocationListEntry[];
  total_with_coordinates: number;
}

interface GlobalOverview {
  donors: DonorOverviewStats;
  patrons: PatronOverviewStats;
  aggregate_identities: AggregateIdentityStats;
  locations: LocationOverview;
}

interface ApiResponse {
  filters: {
    from_date: string;
    to_date: string;
    fiscal_year?: string;
    label?: string;
    generated_on?: string;
  };
  available_fiscal_years: FiscalYearOption[];
  views: Record<BreakdownView, ViewPayload>;
  seva_types: BreakdownResponse;
  seva_subtypes: BreakdownResponse;
  preachers: BreakdownResponse;
  preacher_categories: BreakdownResponse;
  available_companies: AvailableCompany[];
  selected_companies: string[];
  global_overview: GlobalOverview;
}

interface Filters {
  period_type: 'date_range' | 'fiscal_year';
  from_date: string;
  to_date: string;
  fiscal_year: string;
}

type BreakdownView = 'included' | 'excluded' | 'complete';

type BreakdownRow = BreakdownEntry;

type StoredState = {
  filters?: Filters;
  companies?: string[];
};

const defaultFromDate = format(subDays(new Date(), 30), 'yyyy-MM-dd');
const defaultToDate = format(new Date(), 'yyyy-MM-dd');

const pieColors = ['#3182CE', '#2F855A', '#DD6B20', '#805AD5', '#D53F8C', '#718096'];
const LOCAL_STORAGE_KEY = 'dhananjaya_donation_insights_filters';

const loadStoredState = (): StoredState | null => {
  if (typeof window === 'undefined') {
    return null;
  }
  try {
    const raw = window.localStorage.getItem(LOCAL_STORAGE_KEY);
    if (!raw) {
      return null;
    }
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === 'object' ? (parsed as StoredState) : null;
  } catch (error) {
    console.warn('Failed to parse stored donation insights filters', error);
    return null;
  }
};

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value || 0);
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat('en-IN').format(value || 0);
}

function formatDateValue(value?: string): string {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return format(date, 'dd MMM yyyy');
}

function formatShortNumber(value: number): string {
  const abs = Math.abs(value);
  const formatWithUnit = (val: number, unit: string) => {
    const formatted = val >= 10 ? Math.round(val).toString() : val.toFixed(1);
    return `${formatted.replace(/\.0$/, '')}${unit}`;
  };
  if (abs >= 1e7) {
    return formatWithUnit(value / 1e7, 'Cr');
  }
  if (abs >= 1e5) {
    return formatWithUnit(value / 1e5, 'L');
  }
  if (abs >= 1e3) {
    return formatWithUnit(value / 1e3, 'K');
  }
  return formatNumber(value);
}

function formatCompactCurrency(value: number): string {
  if (!value) {
    return '₹0';
  }
  const sign = value < 0 ? '- ' : '';
  const formatted = formatShortNumber(Math.abs(value));
  const amount = formatted.startsWith('₹') ? formatted : `₹${formatted}`;
  return `${sign}${amount}`.trim();
}

const BREAKDOWN_OPTIONS: Array<{
  value: BreakdownView;
  label: string;
  colorScheme: ButtonProps['colorScheme'];
}> = [
  { value: 'included', label: 'Included', colorScheme: 'blue' },
  { value: 'excluded', label: 'Excluded', colorScheme: 'orange' },
  { value: 'complete', label: 'Complete', colorScheme: 'purple' },
];

const DonationInsightsPage = () => {
  const [filters, setFilters] = useState<Filters>(() => {
    const stored = loadStoredState();
    return (
      stored?.filters ?? {
        period_type: 'date_range',
        from_date: defaultFromDate,
        to_date: defaultToDate,
        fiscal_year: '',
      }
    );
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<ApiResponse | null>(null);
  const [fiscalYears, setFiscalYears] = useState<FiscalYearOption[]>([]);
  const [availableCompanies, setAvailableCompanies] = useState<AvailableCompany[]>([]);
  const [selectedCompanies, setSelectedCompanies] = useState<string[]>(() => {
    const stored = loadStoredState();
    return stored?.companies ?? [];
  });
  const [breakdownView, setBreakdownView] = useState<BreakdownView>('complete');
  const [exporting, setExporting] = useState(false);
  const toast = useToast();

  const fetchData = useCallback(
    async (opts: Filters, companiesSelection: string[]) => {
      const payload: Record<string, string> = {};
      if (opts.period_type === 'date_range') {
        if (!opts.from_date || !opts.to_date) {
          setError('Please select both From and To dates.');
          return;
        }
        payload.from_date = opts.from_date;
        payload.to_date = opts.to_date;
      } else {
        if (!opts.fiscal_year) {
          setError('Please choose a Fiscal Year.');
          return;
        }
        payload.fiscal_year = opts.fiscal_year;
      }

      if (companiesSelection.length) {
        payload.companies = companiesSelection.join(',');
      }

      setLoading(true);
      setError(null);

      try {
        const response = await fetchDonationInsights(payload);
        const payloadData = response.data as ApiResponse | { message: ApiResponse };
        const content =
          payloadData && typeof payloadData === 'object' && 'message' in payloadData
            ? payloadData.message
            : payloadData;

        if (!content || typeof content !== 'object') {
          throw new Error('Unexpected response from server.');
        }

        const typed = content as Partial<ApiResponse>;
        if (!typed.filters) {
          throw new Error('Donation insights data is missing filter metadata.');
        }
        if (!typed.views) {
          throw new Error('Donation insights data is missing view aggregates.');
        }

        const availableFiscalYears = typed.available_fiscal_years ?? [];
        setFiscalYears(availableFiscalYears);

        const availableCompanyObjects = typed.available_companies ?? [];
        setAvailableCompanies(availableCompanyObjects);
        const availableCompanyNamesFromResponse = availableCompanyObjects.map((item) => item.name);

        const backendSelection = typed.selected_companies ?? companiesSelection;
        const initialSelection = backendSelection.length ? backendSelection : companiesSelection;
        const cleanedSelection = initialSelection.filter((name) =>
          availableCompanyNamesFromResponse.includes(name)
        );
        const orderedSelection = availableCompanyNamesFromResponse.filter((name) =>
          cleanedSelection.includes(name)
        );
        const nextSelection =
          orderedSelection.length > 0
            ? orderedSelection
            : availableCompanyNamesFromResponse.length > 0
            ? availableCompanyNamesFromResponse
            : [];
        setSelectedCompanies(nextSelection);

        const fullData = typed as ApiResponse;
        setData(fullData);

        if (typeof window !== 'undefined') {
          window.localStorage.setItem(
            LOCAL_STORAGE_KEY,
            JSON.stringify({
              filters: opts,
              companies: nextSelection,
            })
          );
        }
      } catch (err: any) {
        const message = err?.response?.data?.message || err?.message || 'Unable to fetch insights.';
        setData(null);
        setError(message);
        toast({
          title: 'Failed to load donation insights',
          description: message,
          status: 'error',
          duration: 6000,
          isClosable: true,
        });
      } finally {
        setLoading(false);
      }
    },
    [toast]
  );

  useEffect(() => {
    fetchData(filters, selectedCompanies);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleApply = () => {
    fetchData(filters, selectedCompanies);
  };

  const handleReset = () => {
    const reset: Filters = {
      period_type: 'date_range',
      from_date: defaultFromDate,
      to_date: defaultToDate,
      fiscal_year: '',
    };
    const resetCompanies = availableCompanyNames.length > 0 ? availableCompanyNames : selectedCompanies;
    setFilters(reset);
    setSelectedCompanies(resetCompanies);
    fetchData(reset, resetCompanies);
  };

  const showDateRange = filters.period_type === 'date_range';

  const activeViewData = useMemo(() => (data ? data.views?.[breakdownView] ?? null : null), [data, breakdownView]);

  const monthlyData = useMemo(() => {
    if (!activeViewData?.monthly_trends) return [];
    return activeViewData.monthly_trends.map((row) => ({
      ...row,
      amount_value: row.total_amount,
    }));
  }, [activeViewData]);

  const paymentData = activeViewData?.payment_methods || [];
  const companyData = activeViewData?.companies || [];
  const highlights = activeViewData?.highlights;
  const summary = activeViewData?.summary;
  const topDonors = activeViewData?.top_donors || [];
  const topPatrons = activeViewData?.top_patrons || [];
  const currentMonth = activeViewData?.current_month;
  const currentPaymentMethods = currentMonth?.by_payment_method || [];
  const excluded = activeViewData?.excluded;

  const globalOverview = data?.global_overview;
  const donorOverview = globalOverview?.donors;
  const patronOverview = globalOverview?.patrons;
  const aggregateOverview = globalOverview?.aggregate_identities;

  const availableCompanyNames = useMemo(() => availableCompanies.map((item) => item.name), [availableCompanies]);

  const companyLabelMap = useMemo(() => {
    const map: Record<string, string> = {};
    availableCompanies.forEach((item) => {
      map[item.name] = item.label || item.name;
    });
    return map;
  }, [availableCompanies]);

  const isIndeterminateCompanies =
    selectedCompanies.length > 0 && selectedCompanies.length < availableCompanies.length;

  const handleSelectAllCompanies = () => {
    setSelectedCompanies((prev) => (prev.length === availableCompanyNames.length ? [] : availableCompanyNames));
  };

  const toggleCompanySelection = (companyName: string) => {
    setSelectedCompanies((prev) => {
      let next: string[];
      if (prev.includes(companyName)) {
        next = prev.filter((name) => name !== companyName);
      } else {
        next = [...prev, companyName];
      }
      const unique = Array.from(new Set(next));
      if (!availableCompanyNames.length) {
        return unique;
      }
      return availableCompanyNames.filter((name) => unique.includes(name));
    });
  };

  const companyButtonLabel = useMemo(() => {
    if (!availableCompanies.length) {
      return 'Companies';
    }
    if (selectedCompanies.length === availableCompanies.length) {
      return 'All Companies';
    }
    if (selectedCompanies.length === 0) {
      return 'No Company';
    }
    const first = companyLabelMap[selectedCompanies[0]] || selectedCompanies[0];
    if (selectedCompanies.length === 1) {
      return first;
    }
    return `${first} +${selectedCompanies.length - 1}`;
  }, [availableCompanies, selectedCompanies, companyLabelMap]);

  const getBreakdownViewData = (
    breakdown: BreakdownResponse,
    view: BreakdownView
  ): {
    label: string;
    amount: number;
    count: number;
    list: BreakdownRow[];
  } => {
    const summaryData = breakdown.summary;
    if (view === 'included') {
      return {
        label: 'Included',
        amount: summaryData.included_amount,
        count: summaryData.included_count,
        list: breakdown.included,
      };
    }
    if (view === 'excluded') {
      return {
        label: 'Excluded',
        amount: summaryData.excluded_amount,
        count: summaryData.excluded_count,
        list: breakdown.excluded,
      };
    }

    const combinedMap = new Map<string, BreakdownRow>();
    const accumulate = (row: BreakdownRow) => {
      const key = `${row.id ?? row.label}`;
      const existing = combinedMap.get(key);
      if (existing) {
        existing.total_amount += row.total_amount;
        existing.receipt_count += row.receipt_count;
        existing.average =
          existing.receipt_count > 0 ? existing.total_amount / existing.receipt_count : 0;
      } else {
        combinedMap.set(key, { ...row });
      }
    };

    breakdown.included.forEach(accumulate);
    breakdown.excluded.forEach(accumulate);

    const list = Array.from(combinedMap.values()).sort((a, b) => b.total_amount - a.total_amount);

    return {
      label: 'Complete',
      amount: summaryData.included_amount + summaryData.excluded_amount,
      count: summaryData.included_count + summaryData.excluded_count,
      list,
    };
  };

  const renderBreakdownSection = (
    title: string,
    breakdown?: BreakdownResponse,
    view: BreakdownView = 'included'
  ) => {
    if (!breakdown) {
      return null;
    }
    const viewData = getBreakdownViewData(breakdown, view);
    const currentList = viewData.list;
    const chartData = currentList.slice(0, 10).map((item) => ({
      label: item.label,
      total_amount: item.total_amount,
      receipts: item.receipt_count,
    }));

    return (
      <Box bg="white" shadow="sm" borderRadius="lg" p={6}>
        <Flex justify="space-between" align="center" mb={4} gap={4} flexWrap="wrap">
          <Heading size="md">{title}</Heading>
        </Flex>
        <Text fontSize="sm" color="gray.600" mb={4}>
          {viewData.label} amount <strong>{formatCurrency(viewData.amount)}</strong> ·{' '}
          {formatNumber(viewData.count)} receipts
        </Text>
        <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
          <Box h="280px">
            {chartData.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 60 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="label" tick={{ fontSize: 11 }} interval={0} angle={-30} textAnchor="end" height={70} />
                  <YAxis yAxisId="left" tickFormatter={(value) => formatShortNumber(value as number)} />
                  <YAxis
                    yAxisId="right"
                    orientation="right"
                    tickFormatter={(value) => formatNumber(Math.round(value as number))}
                  />
                  <Tooltip
                    formatter={(value, name) =>
                      name && name.toString().toLowerCase() === 'receipts'
                        ? formatNumber(value as number)
                        : formatCurrency(value as number)
                    }
                  />
                  <Legend />
                  <Bar yAxisId="left" dataKey="total_amount" name="Amount" fill="#2B6CB0" radius={[4, 4, 0, 0]} />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="receipts"
                    name="Receipts"
                    stroke="#DD6B20"
                    strokeWidth={2}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            ) : (
              <Flex align="center" justify="center" h="100%">
                <Text color="gray.500">No data available.</Text>
              </Flex>
            )}
          </Box>
          <Box borderWidth="1px" borderColor="gray.100" borderRadius="lg" p={2} maxH="260px" overflowY="auto">
            <Table size="sm" variant="simple">
              <Thead position="sticky" top={0} bg="gray.50" zIndex={1}>
                <Tr>
                  <Th>#</Th>
                  <Th>Label</Th>
                  <Th isNumeric>Amount</Th>
                  <Th isNumeric>Receipts</Th>
                </Tr>
              </Thead>
              <Tbody>
                {currentList.map((row, index) => (
                  <Tr key={`${title}-${view}-${row.id ?? index}`}>
                    <Td>{index + 1}</Td>
                    <Td>{row.label}</Td>
                    <Td isNumeric>{formatCurrency(row.total_amount)}</Td>
                    <Td isNumeric>{formatNumber(row.receipt_count)}</Td>
                  </Tr>
                ))}
                {!currentList.length && (
                  <Tr>
                    <Td colSpan={4}>
                      <Text color="gray.500" textAlign="center">
                        No entries found.
                      </Text>
                    </Td>
                  </Tr>
                )}
              </Tbody>
            </Table>
          </Box>
        </SimpleGrid>
      </Box>
    );
  };

  const status = useMemo(() => {
    if (error) {
      return { label: 'Failed', colorScheme: 'red' } as const;
    }
    if (loading) {
      return { label: 'Loading', colorScheme: 'orange' } as const;
    }
    if (data) {
      return { label: 'Ready', colorScheme: 'green' } as const;
    }
    return null;
  }, [data, loading, error]);

  const handleExportPdf = useCallback(async () => {
    if (!data) {
      toast({
        title: 'Unable to export',
        description: 'Report content is not ready yet. Apply filters to load data first.',
        status: 'error',
        duration: 4000,
        isClosable: true,
      });
      return;
    }

    try {
      setExporting(true);
      const pdf = new jsPDF('p', 'mm', 'a4');
      const pageWidth = pdf.internal.pageSize.getWidth();
      let cursor = 18;

      const addSectionTitle = (title: string, topPadding = 6) => {
        cursor += topPadding;
        pdf.setFontSize(13);
        pdf.text(title, 15, cursor);
        cursor += 2;
      };

      const addTable = (title: string, head: string[], body: (string | number)[][]) => {
        if (!body.length) {
          return;
        }
        addSectionTitle(title);
        autoTable(pdf, {
          startY: cursor + 4,
          head: [head],
          body,
          styles: { fontSize: 9, cellPadding: 2 },
          headStyles: { fillColor: [249, 115, 22] },
          margin: { left: 15, right: 15 },
        });
        const finalY = (pdf as any).lastAutoTable?.finalY ?? cursor;
        cursor = finalY + 8;
      };

      pdf.setFontSize(18);
      pdf.text('Donation Insights Report', pageWidth / 2, cursor, { align: 'center' });
      pdf.setFontSize(11);
      cursor += 6;
      pdf.text(`Generated: ${formatDateValue(data.filters.generated_on)}`, 15, cursor);
      cursor += 6;
      pdf.text(
        `Period: ${formatDateValue(data.filters.from_date)} – ${formatDateValue(data.filters.to_date)}`,
        15,
        cursor
      );
      cursor += 4;

      if (summary) {
        const summaryRows: (string | number)[][] = [
          ['Total Donations', formatCurrency(summary.total_amount)],
          ['Receipts', formatNumber(summary.total_receipts)],
          ['Average Donation', formatCurrency(summary.average_donation)],
          ['Unique Donors', formatNumber(summary.unique_donors)],
          ['Unique Patrons', formatNumber(summary.unique_patrons)],
        ];
        addTable('Overview Summary', ['Metric', 'Value'], summaryRows);
      }

      if (highlights) {
        const highlightRows: (string | number)[][] = [];
        if (typeof highlights.overall_growth_pct === 'number') {
          highlightRows.push(['Overall Growth', `${highlights.overall_growth_pct}%`]);
        }
        if (highlights.best_month) {
          highlightRows.push([
            'Best Month',
            `${highlights.best_month.label} (${formatCurrency(highlights.best_month.total_amount)})`,
          ]);
        }
        if (highlights.worst_month) {
          highlightRows.push([
            'Toughest Month',
            `${highlights.worst_month.label} (${formatCurrency(highlights.worst_month.total_amount)})`,
          ]);
        }
        if (highlights.recent_momentum) {
          highlightRows.push(['Recent Momentum', highlights.recent_momentum.toUpperCase()]);
        }
        addTable('Highlights', ['Detail', 'Value'], highlightRows);
      }

      if (monthlyData.length) {
        const monthlyRows = monthlyData.map((row) => [
          row.label,
          formatCurrency(row.total_amount),
          formatNumber(row.receipt_count),
          formatCurrency(row.average_donation),
        ]);
        addTable('Monthly Trends', ['Month', 'Amount', 'Receipts', 'Average'], monthlyRows);
      }

      if (paymentData.length) {
        const paymentRows = paymentData.map((method) => [
          method.payment_method || 'Unknown',
          formatCurrency(method.total_amount),
          formatNumber(method.receipt_count),
        ]);
        addTable('Payment Methods', ['Method', 'Amount', 'Receipts'], paymentRows);
      }

      if (companyData.length) {
        const companyRows = companyData.map((company) => [
          company.company || 'Unknown',
          formatCurrency(company.total_amount),
          formatNumber(company.receipt_count),
        ]);
        addTable('Company Contributions', ['Company', 'Amount', 'Receipts'], companyRows);
      }

      if (currentMonth) {
        const currentRows: (string | number)[][] = [
          ['Realized Amount', `${formatCurrency(currentMonth.realized_amount)} (${formatNumber(currentMonth.realized_count)} receipts)`],
          ['Acknowledged Amount', `${formatCurrency(currentMonth.acknowledged_amount)} (${formatNumber(currentMonth.acknowledged_count)} receipts)`],
          ['Total Amount', `${formatCurrency(currentMonth.total_amount)} (${formatNumber(currentMonth.total_count)} receipts)`],
        ];
        addTable('Current Month Snapshot', ['Metric', 'Value'], currentRows);

        if (currentPaymentMethods.length) {
          const currentMethodRows = currentPaymentMethods.map((method) => [
            method.payment_method,
            formatCurrency(method.total_amount),
            formatNumber(method.receipt_count),
          ]);
          addTable('Current Month by Payment Method', ['Method', 'Amount', 'Receipts'], currentMethodRows);
        }
      }

      if (excluded && excluded.total_count) {
        const excludedRows = [
          ['Total Excluded Amount', formatCurrency(excluded.total_amount)],
          ['Total Excluded Receipts', formatNumber(excluded.total_count)],
        ];
        addTable('Excluded Receipts Summary', ['Metric', 'Value'], excludedRows);

        if (excluded.reasons?.length) {
          const reasonRows = excluded.reasons.map((reason) => [
            reason.label,
            formatNumber(reason.count),
            formatCurrency(reason.amount),
          ]);
          addTable('Excluded Receipts – Top Reasons', ['Reason', 'Count', 'Amount'], reasonRows);
        }
      }

      if (donorOverview) {
        const donorRows: (string | number)[][] = [
          ['Unique Identities', formatNumber(donorOverview.total_identities)],
          ['Donor Records', formatNumber(donorOverview.total_donors)],
          ['Active (Status)', formatNumber(donorOverview.active_status)],
          ['Dormant (Status)', formatNumber(donorOverview.dormant_status)],
          ['Donated in Last 3 Years', formatNumber(donorOverview.active_recent)],
          ['Donated This FY', formatNumber(donorOverview.donated_this_year)],
          ['New Donors This FY', formatNumber(donorOverview.new_last_year)],
          ['New Donors Previous FY', formatNumber(donorOverview.new_previous_year)],
          [
            'Growth vs Previous FY',
            donorOverview.growth_rate_pct !== null ? `${donorOverview.growth_rate_pct.toFixed(2)}%` : 'N/A',
          ],
        ];
        addTable('Donor Overview', ['Metric', 'Value'], donorRows);
      }

      if (topDonors.length) {
        const topDonorRows = topDonors.map((donor) => [
          donor.label,
          formatCurrency(donor.total_amount),
          formatNumber(donor.receipt_count),
          formatDateValue(donor.last_receipt ?? undefined),
        ]);
        addTable('Top Donors', ['Donor', 'Amount', 'Receipts', 'Last Receipt'], topDonorRows);
      }

      if (patronOverview) {
        const patronRows: (string | number)[][] = [
          ['Total Patrons', formatNumber(patronOverview.total_patrons)],
          ['Active (Last 3 Years)', formatNumber(patronOverview.active_recent)],
          ['Giving This FY', formatNumber(patronOverview.donated_this_year)],
          ['Committed Amount', formatCurrency(patronOverview.committed_total)],
          ['Completed Amount', formatCurrency(patronOverview.donated_total)],
          ['Remaining Amount', formatCurrency(patronOverview.remaining_total)],
          ['New Patrons This FY', formatNumber(patronOverview.new_last_year)],
          ['New Patrons Previous FY', formatNumber(patronOverview.new_previous_year)],
          [
            'Growth vs Previous FY',
            patronOverview.growth_rate_pct !== null ? `${patronOverview.growth_rate_pct.toFixed(2)}%` : 'N/A',
          ],
        ];
        addTable('Patron Overview', ['Metric', 'Value'], patronRows);

        if (patronOverview.categories?.length) {
          const categoryRows = patronOverview.categories.map((category) => [
            category.label || category.seva_type || 'Unspecified',
            formatNumber(category.patron_count),
            formatCurrency(category.committed_amount),
            formatCurrency(category.donated_amount),
            formatCurrency(category.remaining_amount),
            category.completion_pct !== null ? `${Math.min(100, Math.round(category.completion_pct))}%` : 'N/A',
            formatNumber(category.fulfilled_count),
          ]);
          addTable(
            'Commitment by Category',
            ['Category', 'Patrons', 'Committed', 'Completed', 'Remaining', 'Completion %', 'Fulfilled'],
            categoryRows
          );
        }
      }

      if (topPatrons.length) {
        const topPatronRows = topPatrons.map((patron) => [
          patron.label,
          formatCurrency(patron.total_amount),
          formatNumber(patron.receipt_count),
          formatDateValue(patron.last_receipt ?? undefined),
        ]);
        addTable('Top Patrons', ['Patron', 'Amount', 'Receipts', 'Last Receipt'], topPatronRows);
      }

      if (aggregateOverview) {
        const aggregateRows: (string | number)[][] = [
          ['Total Identities', formatNumber(aggregateOverview.total_identities)],
          ['Linked Donors', formatNumber(aggregateOverview.linked_donors)],
          ['Linked Patrons', formatNumber(aggregateOverview.linked_patrons)],
          [
            'Avg Donors per Identity',
            aggregateOverview.average_donors_per_identity !== null
              ? aggregateOverview.average_donors_per_identity.toFixed(2)
              : 'N/A',
          ],
          ['Fiscal Year Context', aggregateOverview.fiscal_year],
        ];
        addTable('Aggregate Identities Snapshot', ['Metric', 'Value'], aggregateRows);
      }

      const filename = `donation-insights-${format(new Date(), 'yyyyMMdd-HHmmss')}.pdf`;
      pdf.save(filename);
      toast({
        title: 'PDF ready',
        description: 'Donation insights exported successfully.',
        status: 'success',
        duration: 4000,
        isClosable: true,
      });
    } catch (err) {
      console.error('Failed to export donation insights PDF', err);
      toast({
        title: 'Unable to export PDF',
        description: 'Something went wrong while generating the PDF. Please try again.',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setExporting(false);
    }
  }, [data, summary, highlights, monthlyData, paymentData, companyData, currentMonth, currentPaymentMethods, excluded, donorOverview, topDonors, patronOverview, topPatrons, aggregateOverview, toast]);

  return (
    <Box bg="gray.50" minH="100vh" py={10} px={{ base: 4, md: 10 }}>
      <PageHeader
        title="Donation Insights"
        status={status}
        backTo="/"
      >
        <Stack direction="row" spacing={3} align="center">
          {loading ? <Spinner size="sm" /> : null}
          <Button
            size="sm"
            colorScheme="orange"
            leftIcon={<FiDownload />}
            onClick={handleExportPdf}
            isDisabled={!data || loading}
            isLoading={exporting}
            loadingText="Preparing"
          >
            Export PDF
          </Button>
        </Stack>
      </PageHeader>

      <Box>
        <Box position="sticky" top={{ base: 2, md: 4 }} zIndex={30} mb={6}>
          <Stack spacing={3}>
            <Box bg="white" shadow="md" borderRadius="lg" p={{ base: 4, md: 6 }}>
              <SimpleGrid columns={{ base: 1, md: 5, xl: 6 }} spacing={4} alignItems="end">
                <Box>
                  <Text fontSize="sm" mb={1} fontWeight="medium">
                    Period
                  </Text>
                  <Select
                    value={filters.period_type}
                    onChange={(event) =>
                      setFilters((prev) => ({
                        ...prev,
                        period_type: event.target.value as Filters['period_type'],
                      }))
                    }
                  >
                    <option value="date_range">Date Range</option>
                    <option value="fiscal_year">Fiscal Year</option>
                  </Select>
                </Box>

                {showDateRange ? (
                  <>
                    <Box>
                      <Text fontSize="sm" mb={1} fontWeight="medium">
                        From Date
                      </Text>
                      <Input
                        type="date"
                        value={filters.from_date}
                        onChange={(event) => setFilters((prev) => ({ ...prev, from_date: event.target.value }))}
                      />
                    </Box>
                    <Box>
                      <Text fontSize="sm" mb={1} fontWeight="medium">
                        To Date
                      </Text>
                      <Input
                        type="date"
                        value={filters.to_date}
                        onChange={(event) => setFilters((prev) => ({ ...prev, to_date: event.target.value }))}
                      />
                    </Box>
                  </>
                ) : (
                  <Box>
                    <Text fontSize="sm" mb={1} fontWeight="medium">
                      Fiscal Year
                    </Text>
                    <Select
                      placeholder="Select fiscal year"
                      value={filters.fiscal_year}
                      onChange={(event) => setFilters((prev) => ({ ...prev, fiscal_year: event.target.value }))}
                    >
                      {fiscalYears.map((fy) => (
                        <option key={fy.name} value={fy.name}>
                          {fy.label || fy.name}
                        </option>
                      ))}
                    </Select>
                  </Box>
                )}

                <Box>
                  <Text fontSize="sm" mb={1} fontWeight="medium">
                    Companies
                  </Text>
                  <Menu closeOnSelect={false}>
                    <MenuButton
                      as={Button}
                      variant="outline"
                      rightIcon={<ChevronDownIcon />}
                      width="100%"
                      justifyContent="space-between"
                      title={
                        selectedCompanies.length
                          ? selectedCompanies.map((name) => companyLabelMap[name] || name).join(', ')
                          : 'No Company'
                      }
                      sx={{
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                      }}
                    >
                      {companyButtonLabel}
                    </MenuButton>
                    <MenuList maxH="260px" overflowY="auto" minW="260px">
                      <Box px={3} py={2}>
                        <Checkbox
                          isChecked={
                            availableCompanies.length > 0 && selectedCompanies.length === availableCompanies.length
                          }
                          isIndeterminate={isIndeterminateCompanies}
                          onChange={handleSelectAllCompanies}
                        >
                          Select All
                        </Checkbox>
                        <Stack mt={2} spacing={1}>
                          {availableCompanies.length ? (
                            availableCompanies.map((company) => (
                              <Checkbox
                                key={company.name}
                                isChecked={selectedCompanies.includes(company.name)}
                                onChange={() => toggleCompanySelection(company.name)}
                              >
                                {company.label}
                              </Checkbox>
                            ))
                          ) : (
                            <Text color="gray.500" fontSize="sm">
                              No companies found.
                            </Text>
                          )}
                        </Stack>
                      </Box>
                    </MenuList>
                  </Menu>
                </Box>

                <Flex gap={3} justify={{ base: 'flex-start', md: 'flex-end' }}>
                  <Button variant="outline" onClick={handleReset} isDisabled={loading}>
                    Reset
                  </Button>
                  <Button colorScheme="orange" onClick={handleApply} isLoading={loading}>
                    Apply Filters
                  </Button>
                </Flex>
              </SimpleGrid>
            </Box>
          </Stack>
        </Box>

        {error && (
          <Alert status="error" mb={6} borderRadius="md">
            <AlertIcon />
            {error}
          </Alert>
        )}

        {loading && !data ? (
          <Flex justify="center" align="center" minH="200px">
            <Spinner size="xl" />
          </Flex>
        ) : null}

        {!loading && data && (
          <Stack spacing={4}>
            <Box>
              <Text fontSize="sm" color="gray.500">
                Updated on {formatDateValue(data.filters.generated_on)}
              </Text>
            </Box>

            <Tabs colorScheme="orange" variant="enclosed" isFitted isLazy>
              <TabList>
                <Tab>Overview</Tab>
                <Tab>Donors</Tab>
                <Tab>Patrons</Tab>
                <Tab>Aggregate</Tab>
              </TabList>
              <TabPanels>
                <TabPanel px={0}>
                  <Stack spacing={6}>
                    <Box bg="white" shadow="sm" borderRadius="lg" p={6}>
                      <Text fontSize="sm" color="gray.600" mb={4}>
                        Showing donations from {formatDateValue(data.filters.from_date)} – {formatDateValue(data.filters.to_date)}
                      </Text>
                      <SimpleGrid columns={{ base: 1, md: 5 }} spacing={4}>
                        <Box bg="gray.50" borderRadius="lg" p={4}>
                          <Text fontSize="sm" color="gray.500">
                            Total Donations
                          </Text>
                          <Heading size="md">{formatCurrency(summary?.total_amount ?? 0)}</Heading>
                        </Box>
                        <Box bg="gray.50" borderRadius="lg" p={4}>
                          <Text fontSize="sm" color="gray.500">
                            Receipts
                          </Text>
                          <Heading size="md">{formatNumber(summary?.total_receipts ?? 0)}</Heading>
                        </Box>
                        <Box bg="gray.50" borderRadius="lg" p={4}>
                          <Text fontSize="sm" color="gray.500">
                            Avg Donation
                          </Text>
                          <Heading size="md">{formatCurrency(summary?.average_donation ?? 0)}</Heading>
                        </Box>
                        <Box bg="gray.50" borderRadius="lg" p={4}>
                          <Text fontSize="sm" color="gray.500">
                            Unique Donors
                          </Text>
                          <Heading size="md">{formatNumber(summary?.unique_donors ?? 0)}</Heading>
                        </Box>
                        <Box bg="gray.50" borderRadius="lg" p={4}>
                          <Text fontSize="sm" color="gray.500">
                            Unique Patrons
                          </Text>
                          <Heading size="md">{formatNumber(summary?.unique_patrons ?? 0)}</Heading>
                        </Box>
                      </SimpleGrid>
                    </Box>

                    {highlights && (
                      <Box bg="white" shadow="sm" borderRadius="lg" p={6}>
                        <Heading size="md" mb={4}>
                          Highlights
                        </Heading>
                        <SimpleGrid columns={{ base: 1, md: 4 }} spacing={4}>
                          <Box bg="gray.50" borderRadius="lg" p={4}>
                            <Text fontSize="sm" color="gray.500">
                              Overall Growth
                            </Text>
                            <Heading size="md">{highlights.overall_growth_pct ?? 0}%</Heading>
                          </Box>
                          {highlights.best_month && (
                            <Box bg="gray.50" borderRadius="lg" p={4}>
                              <Text fontSize="sm" color="gray.500">
                                Best Month
                              </Text>
                              <Heading size="sm">{highlights.best_month.label}</Heading>
                              <Text fontSize="sm" color="gray.500">
                                {formatCurrency(highlights.best_month.total_amount)}
                              </Text>
                            </Box>
                          )}
                          {highlights.worst_month && (
                            <Box bg="gray.50" borderRadius="lg" p={4}>
                              <Text fontSize="sm" color="gray.500">
                                Toughest Month
                              </Text>
                              <Heading size="sm">{highlights.worst_month.label}</Heading>
                              <Text fontSize="sm" color="gray.500">
                                {formatCurrency(highlights.worst_month.total_amount)}
                              </Text>
                            </Box>
                          )}
                          {highlights.recent_momentum && (
                            <Box bg="gray.50" borderRadius="lg" p={4}>
                              <Text fontSize="sm" color="gray.500">
                                Momentum
                              </Text>
                              <Heading size="sm">{highlights.recent_momentum.toUpperCase()}</Heading>
                            </Box>
                          )}
                        </SimpleGrid>
                      </Box>
                    )}

                    <Box bg="white" shadow="sm" borderRadius="lg" p={6}>
                      <Heading size="md" mb={4}>
                        Monthly Donation Trend
                      </Heading>
                      {monthlyData.length ? (
                        <Box h="320px">
                          <ResponsiveContainer width="100%" height="100%">
                            <ComposedChart data={monthlyData}>
                              <CartesianGrid strokeDasharray="3 3" />
                              <XAxis dataKey="label" />
                              <YAxis
                                yAxisId="left"
                                tickFormatter={(value) => formatShortNumber(value as number)}
                                label={{ value: 'Amount', angle: -90, position: 'insideLeft' }}
                              />
                              <YAxis
                                yAxisId="right"
                                orientation="right"
                                label={{ value: 'Receipts', angle: 90, position: 'insideRight' }}
                                tickFormatter={(value) => formatNumber(Math.round(value as number))}
                              />
                              <Tooltip
                                formatter={(value: number, name: string) =>
                                  name === 'Amount' ? formatCurrency(value) : formatNumber(value)
                                }
                              />
                              <Legend />
                              <Bar yAxisId="right" dataKey="receipt_count" fill="#3182CE" name="Receipts" />
                              <Line yAxisId="left" type="monotone" dataKey="amount_value" stroke="#DD6B20" name="Amount" />
                            </ComposedChart>
                          </ResponsiveContainer>
                        </Box>
                      ) : (
                        <Text color="gray.500">No monthly data available for the selected filters.</Text>
                      )}
                    </Box>

                    <SimpleGrid columns={{ base: 1, xl: 2 }} spacing={6}>
                      <Box bg="white" shadow="sm" borderRadius="lg" p={6}>
                        <Heading size="md" mb={4}>
                          Payment Methods
                        </Heading>
                        {paymentData.length ? (
                          <Box h="300px">
                            <ResponsiveContainer width="100%" height="100%">
                              <PieChart>
                                <Pie data={paymentData} dataKey="total_amount" nameKey="payment_method" label={({ name }) => name}>
                                  {paymentData.map((entry, index) => (
                                    <Cell key={`cell-${entry.payment_method}`} fill={pieColors[index % pieColors.length]} />
                                  ))}
                                </Pie>
                                <Tooltip formatter={(value: number) => formatCurrency(value)} />
                                <Legend />
                              </PieChart>
                            </ResponsiveContainer>
                          </Box>
                        ) : (
                          <Text color="gray.500">No payment method data available.</Text>
                        )}
                      </Box>

                      <Box bg="white" shadow="sm" borderRadius="lg" p={6}>
                        <Heading size="md" mb={4}>
                          Company Contributions
                        </Heading>
                        {companyData.length ? (
                          <Box h="300px">
                            <ResponsiveContainer width="100%" height="100%">
                              <PieChart>
                                <Pie data={companyData} dataKey="total_amount" nameKey="company" label={({ name }) => name}>
                                  {companyData.map((entry, index) => (
                                    <Cell key={`company-${entry.company}`} fill={pieColors[index % pieColors.length]} />
                                  ))}
                                </Pie>
                                <Tooltip formatter={(value: number) => formatCurrency(value)} />
                                <Legend />
                              </PieChart>
                            </ResponsiveContainer>
                          </Box>
                        ) : (
                          <Text color="gray.500">No company data available.</Text>
                        )}
                      </Box>
                    </SimpleGrid>

                    <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
                      <Box bg="white" shadow="sm" borderRadius="lg" p={6}>
                        <Heading size="md" mb={4}>
                          Current Month Snapshot
                        </Heading>
                        {currentMonth ? (
                          <Stack spacing={4}>
                            <Text color="gray.600">
                              {formatDateValue(currentMonth.from_date)} – {formatDateValue(currentMonth.to_date)}
                            </Text>
                            <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4}>
                              <Box bg="gray.50" borderRadius="md" p={4}>
                                <Text fontSize="sm" color="gray.500">
                                  Realized Amount
                                </Text>
                                <Heading size="md">{formatCurrency(currentMonth.realized_amount)}</Heading>
                                <Text fontSize="sm" color="gray.500">
                                  {formatNumber(currentMonth.realized_count)} receipts
                                </Text>
                              </Box>
                              <Box bg="gray.50" borderRadius="md" p={4}>
                                <Text fontSize="sm" color="gray.500">
                                  Acknowledged Amount
                                </Text>
                                <Heading size="md">{formatCurrency(currentMonth.acknowledged_amount)}</Heading>
                                <Text fontSize="sm" color="gray.500">
                                  {formatNumber(currentMonth.acknowledged_count)} receipts
                                </Text>
                              </Box>
                              <Box bg="gray.50" borderRadius="md" p={4}>
                                <Text fontSize="sm" color="gray.500">
                                  Total Amount
                                </Text>
                                <Heading size="md">{formatCurrency(currentMonth.total_amount)}</Heading>
                                <Text fontSize="sm" color="gray.500">
                                  {formatNumber(currentMonth.total_count)} receipts
                                </Text>
                              </Box>
                            </SimpleGrid>
                            <Box>
                              <Heading size="sm" mb={3}>
                                Payment Methods
                              </Heading>
                              <SimpleGrid columns={{ base: 1, md: 2 }} spacing={3}>
                                {currentPaymentMethods.map((method) => (
                                  <Box key={method.payment_method} bg="gray.50" borderRadius="md" p={3}>
                                    <Text fontWeight="semibold">{method.payment_method}</Text>
                                    <Text fontSize="sm" color="gray.500">
                                      {formatCurrency(method.total_amount)} · {formatNumber(method.receipt_count)} receipts
                                    </Text>
                                  </Box>
                                ))}
                              </SimpleGrid>
                            </Box>
                          </Stack>
                        ) : (
                          <Text color="gray.500">Current month snapshot not available.</Text>
                        )}
                      </Box>

                      <Box bg="white" shadow="sm" borderRadius="lg" p={6}>
                        <Heading size="md" mb={4}>
                          Excluded Receipts Summary
                        </Heading>
                        {excluded ? (
                          <Stack spacing={4}>
                            <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                              <Box bg="gray.50" borderRadius="md" p={4}>
                                <Text fontSize="sm" color="gray.500">
                                  Excluded Amount
                                </Text>
                                <Heading size="md">{formatCurrency(excluded.total_amount)}</Heading>
                              </Box>
                              <Box bg="gray.50" borderRadius="md" p={4}>
                                <Text fontSize="sm" color="gray.500">
                                  Excluded Receipts
                                </Text>
                                <Heading size="md">{formatNumber(excluded.total_count)}</Heading>
                              </Box>
                            </SimpleGrid>
                            <Heading size="sm">Top Reasons</Heading>
                            <SimpleGrid columns={{ base: 1, md: 2 }} spacing={3}>
                              {excluded.reasons.map((reason) => (
                                <Box key={reason.label} bg="gray.50" borderRadius="md" p={4}>
                                  <Heading size="sm" mb={1}>
                                    {reason.label}
                                  </Heading>
                                  <Text fontSize="sm" color="gray.500">
                                    {formatNumber(reason.count)} receipts
                                  </Text>
                                  <Text fontSize="sm" color="gray.500">
                                    {formatCurrency(reason.amount)} amount
                                  </Text>
                                </Box>
                              ))}
                            </SimpleGrid>
                            <Text fontSize="sm" color="gray.600">
                              Receipts shown here did not pass one or more relevance checks (seva type/subtype or preacher include flags).
                              Switch the floating toggle to "Excluded" to review them inside the charts and tables above.
                            </Text>
                          </Stack>
                        ) : (
                          <Text color="gray.500">All receipts are considered relevant in this analysis.</Text>
                        )}
                      </Box>
                    </SimpleGrid>
                  </Stack>
                </TabPanel>

                <TabPanel px={0}>
                  <Stack spacing={6}>
                    {donorOverview && (
                      <Box bg="white" shadow="sm" borderRadius="lg" p={6}>
                        <Heading size="md" mb={4}>
                          Donor Overview (All Time)
                        </Heading>
                        <SimpleGrid columns={{ base: 1, sm: 2, lg: 3, xl: 6 }} spacing={4}>
                          <Box bg="gray.50" borderRadius="lg" p={4}>
                            <Text fontSize="sm" color="gray.500">
                              Unique Donor Identities
                            </Text>
                            <Heading size="md">{formatNumber(donorOverview.total_identities)}</Heading>
                          </Box>
                          <Box bg="gray.50" borderRadius="lg" p={4}>
                            <Text fontSize="sm" color="gray.500">
                              Donor Records
                            </Text>
                            <Heading size="md">{formatNumber(donorOverview.total_donors)}</Heading>
                          </Box>
                          <Box bg="gray.50" borderRadius="lg" p={4}>
                            <Text fontSize="sm" color="gray.500">
                              Active (Status)
                            </Text>
                            <Heading size="md">{formatNumber(donorOverview.active_status)}</Heading>
                          </Box>
                          <Box bg="gray.50" borderRadius="lg" p={4}>
                            <Text fontSize="sm" color="gray.500">
                              Dormant (Status)
                            </Text>
                            <Heading size="md">{formatNumber(donorOverview.dormant_status)}</Heading>
                          </Box>
                          <Box bg="gray.50" borderRadius="lg" p={4}>
                            <Text fontSize="sm" color="gray.500">
                              Donated in Last 3 Years
                            </Text>
                            <Heading size="md">{formatNumber(donorOverview.active_recent)}</Heading>
                          </Box>
                          <Box bg="gray.50" borderRadius="lg" p={4}>
                            <Text fontSize="sm" color="gray.500">
                              Donated This FY
                            </Text>
                            <Heading size="md">{formatNumber(donorOverview.donated_this_year)}</Heading>
                          </Box>
                        </SimpleGrid>
                        <Stack mt={4} spacing={1} color="gray.600">
                          <Text>
                            New donor records this FY: {formatNumber(donorOverview.new_last_year)} · Previous FY: {formatNumber(donorOverview.new_previous_year)}
                          </Text>
                          <Text>
                            Growth vs previous FY:{' '}
                            {donorOverview.growth_rate_pct !== null
                              ? `${donorOverview.growth_rate_pct >= 0 ? '+' : ''}${donorOverview.growth_rate_pct.toFixed(2)}%`
                              : 'Not available'}
                          </Text>
                        </Stack>
                      </Box>
                    )}

                    <Box bg="white" shadow="sm" borderRadius="lg" p={6}>
                      <Heading size="md" mb={4}>
                        Top Donors
                      </Heading>
                      {topDonors.length ? (
                        <Stack spacing={3}>
                          {topDonors.map((donor) => (
                            <Flex
                              key={donor.id}
                              justify="space-between"
                              align="center"
                              borderWidth="1px"
                              borderColor="gray.200"
                              borderRadius="md"
                              p={3}
                            >
                              <Box>
                                <Heading size="sm">{donor.label}</Heading>
                                <Text fontSize="sm" color="gray.500">
                                  Last donation: {formatDateValue(donor.last_receipt ?? undefined)}
                                </Text>
                              </Box>
                              <Box textAlign="right">
                                <Heading size="sm">{formatCurrency(donor.total_amount)}</Heading>
                                <Text fontSize="sm" color="gray.500">
                                  {formatNumber(donor.receipt_count)} receipts · Avg {formatCurrency(donor.average)}
                                </Text>
                              </Box>
                            </Flex>
                          ))}
                        </Stack>
                      ) : (
                        <Text color="gray.500">No donor data available.</Text>
                      )}
                    </Box>
                  </Stack>
                </TabPanel>

                <TabPanel px={0}>
                  <Stack spacing={6}>
                    {patronOverview && (
                      <Box bg="white" shadow="sm" borderRadius="lg" p={6}>
                        <Heading size="md" mb={4}>
                          Patron Overview (All Time)
                        </Heading>
                        <SimpleGrid columns={{ base: 1, sm: 2, lg: 3, xl: 5 }} spacing={4}>
                          <Box bg="gray.50" borderRadius="lg" p={4}>
                            <Text fontSize="sm" color="gray.500">
                              Total Patrons
                            </Text>
                            <Heading size="md">{formatNumber(patronOverview.total_patrons)}</Heading>
                          </Box>
                          <Box bg="gray.50" borderRadius="lg" p={4}>
                            <Text fontSize="sm" color="gray.500">
                              Active Patrons (3 yrs)
                            </Text>
                            <Heading size="md">{formatNumber(patronOverview.active_recent)}</Heading>
                          </Box>
                          <Box bg="gray.50" borderRadius="lg" p={4}>
                            <Text fontSize="sm" color="gray.500">
                              Patrons Giving This FY
                            </Text>
                            <Heading size="md">{formatNumber(patronOverview.donated_this_year)}</Heading>
                          </Box>
                          <Box bg="gray.50" borderRadius="lg" p={4}>
                            <Text fontSize="sm" color="gray.500">
                              Commitment Completed
                            </Text>
                            <Heading size="md">{formatCompactCurrency(patronOverview.donated_total ?? 0)}</Heading>
                            <Text fontSize="xs" color="gray.600">
                              {formatCompactCurrency(patronOverview.committed_total ?? 0)} committed
                            </Text>
                          </Box>
                          <Box bg="gray.50" borderRadius="lg" p={4}>
                            <Text fontSize="sm" color="gray.500">
                              Remaining Commitment
                            </Text>
                            <Heading size="md">{formatCompactCurrency(patronOverview.remaining_total ?? 0)}</Heading>
                          </Box>
                        </SimpleGrid>
                        <Stack mt={4} spacing={1} color="gray.600">
                          <Text>
                            New patrons this FY: {formatNumber(patronOverview.new_last_year)} · Previous FY: {formatNumber(patronOverview.new_previous_year)}
                          </Text>
                          <Text>
                            Growth vs previous FY:{' '}
                            {patronOverview.growth_rate_pct !== null
                              ? `${patronOverview.growth_rate_pct >= 0 ? '+' : ''}${patronOverview.growth_rate_pct.toFixed(2)}%`
                              : 'Not available'}
                          </Text>
                        </Stack>
                        <Box mt={6}>
                          <Heading size="sm" mb={3}>
                            Commitment by Category
                          </Heading>
                          <Box overflowX="auto">
                            <Table size="sm" variant="simple">
                              <Thead>
                                <Tr>
                                  <Th>Category</Th>
                                  <Th isNumeric>Patrons</Th>
                                  <Th isNumeric>Committed</Th>
                                  <Th isNumeric>Completed</Th>
                                  <Th isNumeric>Remaining</Th>
                                  <Th isNumeric>Completion %</Th>
                                  <Th isNumeric>Fulfilled</Th>
                                </Tr>
                              </Thead>
                              <Tbody>
                                {patronOverview.categories.map((category) => (
                                  <Tr key={category.seva_type || category.label || 'unknown'}>
                                    <Td>{category.label || category.seva_type || 'Unspecified'}</Td>
                                    <Td isNumeric>{formatNumber(category.patron_count)}</Td>
                                    <Td isNumeric>{formatCompactCurrency(category.committed_amount ?? 0)}</Td>
                                    <Td isNumeric>{formatCompactCurrency(category.donated_amount ?? 0)}</Td>
                                    <Td isNumeric>{formatCompactCurrency(category.remaining_amount ?? 0)}</Td>
                                    <Td isNumeric>
                                      {category.completion_pct !== null
                                        ? `${Math.min(100, Math.round(category.completion_pct))}%`
                                        : 'N/A'}
                                    </Td>
                                    <Td isNumeric>{formatNumber(category.fulfilled_count)}</Td>
                                  </Tr>
                                ))}
                              </Tbody>
                            </Table>
                          </Box>
                        </Box>
                      </Box>
                    )}

                    <Box bg="white" shadow="sm" borderRadius="lg" p={6}>
                      <Heading size="md" mb={4}>
                        Top Patrons
                      </Heading>
                      {topPatrons.length ? (
                        <Stack spacing={3}>
                          {topPatrons.map((patron) => (
                            <Flex
                              key={patron.id}
                              justify="space-between"
                              align="center"
                              borderWidth="1px"
                              borderColor="gray.200"
                              borderRadius="md"
                              p={3}
                            >
                              <Box>
                                <Heading size="sm">{patron.label}</Heading>
                                <Text fontSize="sm" color="gray.500">
                                  Last donation: {formatDateValue(patron.last_receipt ?? undefined)}
                                </Text>
                              </Box>
                              <Box textAlign="right">
                                <Heading size="sm">{formatCurrency(patron.total_amount)}</Heading>
                                <Text fontSize="sm" color="gray.500">
                                  {formatNumber(patron.receipt_count)} receipts · Avg {formatCurrency(patron.average)}
                                </Text>
                              </Box>
                            </Flex>
                          ))}
                        </Stack>
                      ) : (
                        <Text color="gray.500">No patron data available.</Text>
                      )}
                    </Box>
                  </Stack>
                </TabPanel>

                <TabPanel px={0}>
                  <Stack spacing={6}>
                    {aggregateOverview && (
                      <Box bg="white" shadow="sm" borderRadius="lg" p={6}>
                        <Heading size="md" mb={4}>
                          Aggregate Identities Snapshot
                        </Heading>
                        <SimpleGrid columns={{ base: 1, sm: 2, lg: 4 }} spacing={4}>
                          <Box bg="gray.50" borderRadius="lg" p={4}>
                            <Text fontSize="sm" color="gray.500">
                              Total Identities
                            </Text>
                            <Heading size="md">{formatNumber(aggregateOverview.total_identities)}</Heading>
                          </Box>
                          <Box bg="gray.50" borderRadius="lg" p={4}>
                            <Text fontSize="sm" color="gray.500">
                              Linked Donors
                            </Text>
                            <Heading size="md">{formatNumber(aggregateOverview.linked_donors)}</Heading>
                          </Box>
                          <Box bg="gray.50" borderRadius="lg" p={4}>
                            <Text fontSize="sm" color="gray.500">
                              Linked Patrons
                            </Text>
                            <Heading size="md">{formatNumber(aggregateOverview.linked_patrons)}</Heading>
                          </Box>
                          <Box bg="gray.50" borderRadius="lg" p={4}>
                            <Text fontSize="sm" color="gray.500">
                              Avg Donors per Identity
                            </Text>
                            <Heading size="md">
                              {aggregateOverview.average_donors_per_identity !== null
                                ? aggregateOverview.average_donors_per_identity.toFixed(2)
                                : 'N/A'}
                            </Heading>
                          </Box>
                        </SimpleGrid>
                        <Text mt={4} fontSize="sm" color="gray.600">
                          Current Fiscal Year Context: {aggregateOverview.fiscal_year}
                        </Text>
                      </Box>
                    )}
                  </Stack>
                </TabPanel>
              </TabPanels>
            </Tabs>
          </Stack>
        )}

        {!loading && !data && !error ? <Text color="gray.500">No data available for the selected filters.</Text> : null}
      </Box>

      {data && (
        <Box
          position="fixed"
          top="50%"
          right={{ base: 3, md: 8 }}
          transform="translateY(-50%)"
          zIndex={40}
          bg="white"
          shadow="lg"
          borderRadius="2xl"
          px={3}
          py={4}
        >
          <Stack spacing={2} align="stretch">
            {BREAKDOWN_OPTIONS.map((option) => (
              <Button
                key={option.value}
                colorScheme={option.colorScheme}
                variant={breakdownView === option.value ? 'solid' : 'outline'}
                onClick={() => setBreakdownView(option.value)}
              >
                {option.label}
              </Button>
            ))}
          </Stack>
        </Box>
      )}
    </Box>
  );
};

export default DonationInsightsPage;

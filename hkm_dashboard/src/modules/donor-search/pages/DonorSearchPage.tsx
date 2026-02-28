import {
  Alert,
  AlertIcon,
  Badge,
  Box,
  Button,
  Flex,
  Heading,
  Input,
  SimpleGrid,
  Spinner,
  Stack,
  Tab,
  TabList,
  TabPanel,
  TabPanels,
  Tabs,
  Table,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tr,
  Link,
} from '@chakra-ui/react';
import { ChangeEvent, Fragment, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import axios from 'axios';
import { searchDonors } from '../../../services/dhananjayaApi';
import { formatCurrency, formatDate, formatNumber } from '../../../utils/formatters';
import PageHeader from '../../../components/shared/PageHeader';

interface DonorContactEntry {
  contact_no?: string | null;
  is_whatsapp?: number | null;
}

interface DonorEmailEntry {
  email?: string | null;
}

interface DonorAddressEntry {
  type?: string | null;
  address_line_1?: string | null;
  address_line_2?: string | null;
  city?: string | null;
  state?: string | null;
  country?: string | null;
  pin_code?: string | null;
  preferred?: number | null;
}

interface DonorChildEntry {
  child_doctype?: string | null;
  child_name?: string | null;
  child_full_name?: string | null;
  donation_count?: number | null;
  total_contribution?: number | null;
  preacher?: string | null;
  preacher_name?: string | null;
}

interface DonorSearchResult {
  name: string;
  primary_name?: string | null;
  status?: string | null;
  total_amount?: number | null;
  donation_count?: number | null;
  last_donation_date?: string | null;
  primary_preacher?: string | null;
  primary_preacher_name?: string | null;
  contact_numbers?: DonorContactEntry[];
  emails?: DonorEmailEntry[];
  addresses?: DonorAddressEntry[];
  children?: DonorChildEntry[];
}

interface DonorSearchResponse {
  results: DonorSearchResult[];
  next_start?: number;
  has_more?: boolean;
}

type DonorSearchFilters = {
  name: string;
  phone: string;
  address: string;
};

const DONOR_SEARCH_PAGE_LENGTH = 10;

const DonorSearchPage = () => {
  const [formValues, setFormValues] = useState<DonorSearchFilters>({
    name: '',
    phone: '',
    address: '',
  });
  const [debouncedValues, setDebouncedValues] = useState<DonorSearchFilters>(formValues);
  const [results, setResults] = useState<DonorSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [nextStart, setNextStart] = useState(0);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const abortRef = useRef<AbortController | null>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      setDebouncedValues(formValues);
    }, 1000);
    return () => window.clearTimeout(timeout);
  }, [formValues]);

  useEffect(() => {
    return () => {
      mountedRef.current = false;
      if (abortRef.current) {
        abortRef.current.abort();
      }
    };
  }, []);

  const activeFilters = useMemo<DonorSearchFilters>(
    () => ({
      name: debouncedValues.name.trim(),
      phone: debouncedValues.phone.trim(),
      address: debouncedValues.address.trim(),
    }),
    [debouncedValues]
  );

  const hasActiveFilters = useMemo(
    () => Object.values(activeFilters).some((value) => value.length > 0),
    [activeFilters]
  );

  const fetchResults = useCallback(
    async (filters: DonorSearchFilters, start: number, reset: boolean) => {
      if (abortRef.current) {
        abortRef.current.abort();
      }

      const controller = new AbortController();
      abortRef.current = controller;

      if (reset) {
        if (mountedRef.current) {
          setLoading(true);
          setError(null);
          setResults([]);
          setHasMore(false);
          setNextStart(0);
          setExpanded({});
        }
      } else if (mountedRef.current) {
        setLoadingMore(true);
      }

      try {
        const response = await searchDonors(
          {
            name_query: filters.name,
            phone_query: filters.phone,
            address_query: filters.address,
            start,
            page_length: DONOR_SEARCH_PAGE_LENGTH,
          },
          controller.signal
        );

        if (!mountedRef.current) {
          return;
        }

        const rawData = response.data as DonorSearchResponse | { message: DonorSearchResponse };
        const payload =
          rawData && typeof rawData === 'object' && 'message' in rawData ? rawData.message : rawData;

        if (!payload || typeof payload !== 'object') {
          throw new Error('Unexpected response from server.');
        }

        const typed = payload as DonorSearchResponse;
        const newResults = Array.isArray(typed.results) ? typed.results : [];

        setResults((prev) => (reset ? newResults : [...prev, ...newResults]));
        setNextStart(typed.next_start ?? start + newResults.length);
        setHasMore(Boolean(typed.has_more));
        setError(null);
      } catch (err) {
        if (axios.isCancel(err)) {
          return;
        }
        if ((err as DOMException)?.name === 'AbortError') {
          return;
        }
        if (!mountedRef.current) {
          return;
        }

        const message =
          (axios.isAxiosError(err) && (err.response?.data?.message as string)) ||
          (err as Error).message ||
          'Unable to fetch donor search results.';
        setError(message);
      } finally {
        if (!mountedRef.current) {
          return;
        }
        if (reset) {
          setLoading(false);
        } else {
          setLoadingMore(false);
        }
      }
    },
    []
  );

  useEffect(() => {
    if (!hasActiveFilters) {
      if (abortRef.current) {
        abortRef.current.abort();
      }
      if (mountedRef.current) {
        setLoading(false);
        setLoadingMore(false);
        setResults([]);
        setHasMore(false);
        setNextStart(0);
        setError(null);
        setExpanded({});
      }
      return;
    }

    fetchResults(activeFilters, 0, true);
  }, [activeFilters, fetchResults, hasActiveFilters]);

  const handleInputChange =
    (key: keyof DonorSearchFilters) =>
    (event: ChangeEvent<HTMLInputElement>) => {
      const value = event.target.value;
      setFormValues((prev) => ({
        ...prev,
        [key]: value,
      }));
    };

  const handleLoadMore = () => {
    if (!hasActiveFilters) {
      return;
    }
    fetchResults(activeFilters, nextStart, false);
  };

  const sortedResults = useMemo(() => {
    return [...results].sort((a, b) => {
      const isActiveA = (a.status || '').toLowerCase() === 'active';
      const isActiveB = (b.status || '').toLowerCase() === 'active';
      if (isActiveA !== isActiveB) {
        return isActiveA ? -1 : 1;
      }

      const donationCountA = a.donation_count ?? 0;
      const donationCountB = b.donation_count ?? 0;
      if (donationCountA !== donationCountB) {
        return donationCountB - donationCountA;
      }

      const nameA = (a.primary_name || a.name || '').toLowerCase();
      const nameB = (b.primary_name || b.name || '').toLowerCase();
      return nameA.localeCompare(nameB);
    });
  }, [results]);

  const toggleExpanded = (name: string) => {
    setExpanded((prev) => ({
      ...prev,
      [name]: !prev[name],
    }));
  };

  const formatAddress = (address: DonorAddressEntry) =>
    [
      address.address_line_1,
      address.address_line_2,
      address.city,
      address.state,
      address.country,
      address.pin_code,
    ]
      .map((part) => part?.trim())
      .filter(Boolean)
      .join(', ');

  const highlightText = (text: string, query: string) => {
    if (!query.trim()) {
      return text;
    }
    const parts = text.split(new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi'));
    return parts.map((part, index) =>
      part.toLowerCase() === query.toLowerCase() ? (
        <Text
          as="mark"
          key={`${part}-${index}`}
          bg="orange.200"
          color="orange.900"
          px={0.5}
          borderRadius="sm"
          fontWeight="semibold"
        >
          {part}
        </Text>
      ) : (
        <Fragment key={`${part}-${index}`}>{part}</Fragment>
      )
    );
  };

  const getStatusColor = (status?: string | null): string => {
    const statusLower = (status || '').toLowerCase();
    if (statusLower === 'active') return 'green';
    if (statusLower === 'dormant') return 'red';
    return 'gray';
  };

  const buildProfileUrl = (doctype?: string | null, name?: string | null): string | null => {
    if (!doctype || !name) {
      return null;
    }
    const slug = doctype.trim().toLowerCase().replace(/\s+/g, '-');
    if (!slug) {
      return null;
    }
    return `/app/${slug}/${encodeURIComponent(name.trim())}`;
  };

  return (
    <Box bg="gray.50" minH="100vh" py={10} px={{ base: 4, md: 10 }}>
      <Stack spacing={6}>
        <PageHeader
          title="Donor Search"
          subtitle="Look up aggregate donor identities by name, mobile number, or address."
          backTo="/"
        />

        <Box bg="white" shadow="sm" borderRadius="lg" p={6}>
          <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4}>
            <Box>
              <Text fontSize="sm" mb={1} fontWeight="medium">
                Name
              </Text>
              <Input
                placeholder="Search by donor name"
                value={formValues.name}
                onChange={handleInputChange('name')}
              />
            </Box>
            <Box>
              <Text fontSize="sm" mb={1} fontWeight="medium">
                Mobile Number
              </Text>
              <Input
                placeholder="Search by mobile number"
                value={formValues.phone}
                onChange={handleInputChange('phone')}
              />
            </Box>
            <Box>
              <Text fontSize="sm" mb={1} fontWeight="medium">
                Address
              </Text>
              <Input
                placeholder="Search by address"
                value={formValues.address}
                onChange={handleInputChange('address')}
              />
            </Box>
          </SimpleGrid>
          {!hasActiveFilters && (
            <Text color="gray.500" fontSize="sm" mt={4}>
              Start typing in any field to look up donor aggregate identities.
            </Text>
          )}
        </Box>

        {error && (
          <Alert status="error" borderRadius="md">
            <AlertIcon />
            {error}
          </Alert>
        )}

        {loading && (
          <Flex justify="center" align="center" minH="200px">
            <Spinner size="xl" />
          </Flex>
        )}

        {!loading && hasActiveFilters && !results.length && !error && (
          <Text color="gray.500">No donors matched your search.</Text>
        )}

        <Stack spacing={4}>
          {sortedResults.map((result) => {
            const displayName = result.primary_name || result.name;
            const isExpanded = expanded[result.name];
            const primaryContactEntry = result.contact_numbers?.find((contact) => contact.contact_no);
            const primaryContactNumber = primaryContactEntry?.contact_no;
            const linkedStats = (result.children || []).reduce(
              (acc, child) => {
                acc.total += 1;
                const type = (child.child_doctype || '').toLowerCase();
                if (type === 'donor') {
                  acc.donors += 1;
                } else if (type === 'patron') {
                  acc.patrons += 1;
                }
                return acc;
              },
              { total: 0, donors: 0, patrons: 0 }
            );
            return (
              <Box key={result.name} bg="white" shadow="sm" borderRadius="lg" p={6}>
                <Flex direction="column" gap={4}>
                  <Flex justify="space-between" align="center" flexWrap="wrap" gap={3}>
                    <Box>
                      <Flex align="center" gap={2} mb={1} flexWrap="wrap">
                        <Box
                          w="10px"
                          h="10px"
                          borderRadius="full"
                          bg={`${getStatusColor(result.status)}.500`}
                          flexShrink={0}
                          title={result.status ?? 'Unknown'}
                        />
                        <Heading size="md">
                          {highlightText(displayName, activeFilters.name)}
                        </Heading>
                        {result.primary_preacher_name && (
                          <Badge colorScheme="orange" fontSize="0.8em" px={2} py={0.5}>
                            {result.primary_preacher_name}
                          </Badge>
                        )}
                      </Flex>
                      <Text color="gray.500" fontSize="sm">
                        ID: {result.name}
                      </Text>
                    </Box>
                  </Flex>
                  <SimpleGrid columns={{ base: 1, sm: 2, lg: 5 }} spacing={3} w="full">
                    <Box bg="gray.50" borderRadius="md" p={3} minW="0">
                      <Text fontSize="xs" textTransform="uppercase" color="gray.500" mb={1}>
                        Lifetime Contribution
                      </Text>
                      <Heading size="sm" isTruncated title={formatCurrency(result.total_amount ?? 0)}>
                        {formatCurrency(result.total_amount ?? 0)}
                      </Heading>
                    </Box>
                    <Box bg="gray.50" borderRadius="md" p={3} minW="0">
                      <Text fontSize="xs" textTransform="uppercase" color="gray.500" mb={1}>
                        Total Donations
                      </Text>
                      <Heading size="sm">{formatNumber(result.donation_count ?? 0)}</Heading>
                    </Box>
                    <Box bg="gray.50" borderRadius="md" p={3} minW="0">
                      <Text fontSize="xs" textTransform="uppercase" color="gray.500" mb={1}>
                        Last Donation
                      </Text>
                      <Heading size="sm" isTruncated title={formatDate(result.last_donation_date ?? undefined)}>
                        {formatDate(result.last_donation_date ?? undefined)}
                      </Heading>
                    </Box>
                    <Box bg="gray.50" borderRadius="md" p={3} minW="0">
                      <Text fontSize="xs" textTransform="uppercase" color="gray.500" mb={1}>
                        Primary Contact
                      </Text>
                      <Heading size="sm" isTruncated>
                        {primaryContactNumber ? (
                          <>
                            {highlightText(primaryContactNumber, activeFilters.phone)}
                            {primaryContactEntry?.is_whatsapp ? (
                              <Text as="span" fontSize="xs" color="green.600" ml={1}>
                                (WA)
                              </Text>
                            ) : null}
                          </>
                        ) : (
                          '-'
                        )}
                      </Heading>
                    </Box>
                    <Box bg="gray.50" borderRadius="md" p={3} minW="0">
                      <Text fontSize="xs" textTransform="uppercase" color="gray.500" mb={1}>
                        Linked Profiles
                      </Text>
                      <Heading size="sm">{formatNumber(linkedStats.total)}</Heading>
                      <Text fontSize="xs" color="gray.500">
                        Donors: {formatNumber(linkedStats.donors)} · Patrons: {formatNumber(linkedStats.patrons)}
                      </Text>
                    </Box>
                  </SimpleGrid>
                </Flex>

                <Button variant="link" mt={4} colorScheme="orange" onClick={() => toggleExpanded(result.name)}>
                  {isExpanded ? 'Hide full details' : 'Show full details'}
                </Button>

                {isExpanded && (
                  <Box mt={4} pt={4} borderTopWidth="1px" borderColor="gray.100">
                    <Tabs colorScheme="orange" variant="enclosed">
                      <TabList>
                        {result.children?.length ? <Tab>Linked Profiles</Tab> : null}
                        {result.contact_numbers?.length ? <Tab>Contact Numbers</Tab> : null}
                        {result.emails?.length ? <Tab>Emails</Tab> : null}
                        {result.addresses?.length ? <Tab>Addresses</Tab> : null}
                      </TabList>

                      <TabPanels>
                        {result.children?.length ? (
                          <TabPanel>
                            <Box overflowX="auto">
                              <Table size="sm" variant="simple">
                                <Thead>
                                  <Tr>
                                    <Th>Name</Th>
                                    <Th>Type</Th>
                                    <Th isNumeric>Total Contribution</Th>
                                    <Th isNumeric>Donations</Th>
                                    <Th>Preacher</Th>
                                  </Tr>
                                </Thead>
                                <Tbody>
                                  {result.children.map((child, index) => (
                                    <Tr key={`${result.name}-child-${index}`}>
                                      <Td>
                                        {child.child_name ? (
                                          <Link
                                            href={buildProfileUrl(child.child_doctype, child.child_name) ?? undefined}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            color="orange.500"
                                            fontWeight="semibold"
                                          >
                                            {child.child_full_name || child.child_name}
                                          </Link>
                                        ) : (
                                          child.child_full_name || child.child_name || '-'
                                        )}
                                      </Td>
                                      <Td>{child.child_doctype}</Td>
                                      <Td isNumeric>{formatCurrency(child.total_contribution ?? 0)}</Td>
                                      <Td isNumeric>{formatNumber(child.donation_count ?? 0)}</Td>
                                      <Td>{child.preacher_name || child.preacher || '-'}</Td>
                                    </Tr>
                                  ))}
                                </Tbody>
                              </Table>
                            </Box>
                          </TabPanel>
                        ) : null}

                        {result.contact_numbers?.length ? (
                          <TabPanel>
                            <SimpleGrid columns={{ base: 1, sm: 2, md: 3 }} spacing={3}>
                              {result.contact_numbers.map((contact, index) => (
                                <Box
                                  key={`${result.name}-contact-${index}`}
                                  borderWidth="1px"
                                  borderColor="gray.200"
                                  borderRadius="md"
                                  p={3}
                                  bg="gray.50"
                                >
                                  <Text fontWeight="medium" color="gray.700">
                                    {highlightText(contact.contact_no || '-', activeFilters.phone)}
                                  </Text>
                                  {contact.is_whatsapp ? (
                                    <Badge colorScheme="green" mt={2} width="fit-content">
                                      WhatsApp
                                    </Badge>
                                  ) : null}
                                </Box>
                              ))}
                            </SimpleGrid>
                          </TabPanel>
                        ) : null}

                        {result.emails?.length ? (
                          <TabPanel>
                            <SimpleGrid columns={{ base: 1, sm: 2, md: 3 }} spacing={3}>
                              {result.emails.map((email, index) => (
                                <Box
                                  key={`${result.name}-email-${index}`}
                                  borderWidth="1px"
                                  borderColor="gray.200"
                                  borderRadius="md"
                                  p={3}
                                  bg="gray.50"
                                >
                                  <Text color="gray.700">{email.email}</Text>
                                </Box>
                              ))}
                            </SimpleGrid>
                          </TabPanel>
                        ) : null}

                        {result.addresses?.length ? (
                          <TabPanel>
                            <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={3}>
                              {result.addresses.map((address, index) => (
                                <Box
                                  key={`${result.name}-address-${index}`}
                                  borderWidth="1px"
                                  borderColor="gray.200"
                                  borderRadius="md"
                                  p={3}
                                  bg="gray.50"
                                >
                                  <Stack direction="row" spacing={2} align="center" flexWrap="wrap" mb={2}>
                                    {address.type ? (
                                      <Badge colorScheme="blue" variant="subtle">
                                        {address.type}
                                      </Badge>
                                    ) : null}
                                    {address.preferred ? (
                                      <Badge colorScheme="green" variant="subtle">
                                        Preferred
                                      </Badge>
                                    ) : null}
                                  </Stack>
                                  <Text color="gray.700" fontSize="sm">
                                    {highlightText(formatAddress(address), activeFilters.address)}
                                  </Text>
                                </Box>
                              ))}
                            </SimpleGrid>
                          </TabPanel>
                        ) : null}
                      </TabPanels>
                    </Tabs>
                  </Box>
                )}
              </Box>
            );
          })}
        </Stack>

        {hasMore && (
          <Flex justify="center">
            <Button onClick={handleLoadMore} isLoading={loadingMore} colorScheme="orange">
              Load more results
            </Button>
          </Flex>
        )}
      </Stack>
    </Box>
  );
};

export default DonorSearchPage;


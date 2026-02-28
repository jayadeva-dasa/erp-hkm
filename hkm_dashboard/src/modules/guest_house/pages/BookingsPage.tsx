// Bookings Search Page
import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Container,
  VStack,
  Heading,
  Text,
  useToast,
  Spinner,
  HStack,
  Badge,
  Flex,
  Icon,
  Button,
  Input,
  InputGroup,
  InputLeftElement,
  SimpleGrid,
  Card,
  CardBody,
  useColorModeValue,
  Select,
  IconButton,
} from '@chakra-ui/react';
import {
  FiSearch,
  FiCalendar,
  FiUser,
  FiDollarSign,
  FiUsers,
  FiEye,
  FiRefreshCw,
} from 'react-icons/fi';
import { guestHouseApi, SearchBookingsParams } from '../api/guestHouseApi';
import BookingDetailModal from '../components/BookingDetailModal';

interface Booking {
  name: string;
  full_name: string;
  from_date: string;
  to_date: string;
  booking_status: string;
  docstatus: number;
  amount: number;
  total_person: number;
  guest_type: string;
  devotee: string | null;
  creation: string;
}

const BookingsPage: React.FC = () => {
  const toast = useToast();
  const bgColor = useColorModeValue('white', 'gray.800');
  const cardBg = useColorModeValue('white', 'gray.700');

  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [selectedBooking, setSelectedBooking] = useState<string | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState<boolean>(false);

  // Search filters
  const [searchText, setSearchText] = useState<string>('');
  const [fromDate, setFromDate] = useState<string>('');
  const [toDate, setToDate] = useState<string>('');
  const [devotee, setDevotee] = useState<string>('');
  const [sortField, setSortField] = useState<string>('creation');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [page, setPage] = useState<number>(0);
  const pageSize = 20;

  const fetchBookings = useCallback(async () => {
    setLoading(true);
    try {
      const params: SearchBookingsParams = {
        page,
        page_size: pageSize,
        search_field: 'full_name',
        search_text: debouncedSearchText?.trim() || undefined,
        from_date: fromDate || undefined,
        to_date: toDate || undefined,
        devotee: devotee?.trim() ? [devotee.trim()] : undefined,
        sort_field: sortField,
        sort_order: sortOrder,
      };

      // Remove undefined values
      Object.keys(params).forEach((key) => {
        if (params[key as keyof SearchBookingsParams] === undefined) {
          delete params[key as keyof SearchBookingsParams];
        }
      });

      const result = await guestHouseApi.searchBookings(params);
      setBookings(Array.isArray(result) ? result : []);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to fetch bookings',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  }, [page, debouncedSearchText, fromDate, toDate, devotee, sortField, sortOrder, pageSize, toast]);

  // Debounce search text - use a separate state to trigger fetch
  const [debouncedSearchText, setDebouncedSearchText] = useState<string>(searchText);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchText(searchText);
      setPage(0);
    }, 500); // 500ms debounce

    return () => clearTimeout(timer);
  }, [searchText]);

  // Auto-fetch when filters change (reset to page 0)
  useEffect(() => {
    setPage(0);
  }, [fromDate, toDate, devotee, sortField, sortOrder]);

  // Fetch when any filter or page changes
  useEffect(() => {
    fetchBookings();
  }, [fetchBookings]);


  const handleBookingClick = (bookingId: string) => {
    setSelectedBooking(bookingId);
    setIsDetailModalOpen(true);
  };

  const getBookingStatus = (booking: Booking) => {
    // docstatus: 0 = Draft, 1 = Submitted, 2 = Cancelled
    if (booking.docstatus === 2) {
      return { text: 'Cancelled', color: 'red' };
    }
    if (booking.docstatus === 1) {
      // Use booking_status field for submitted bookings
      const status = booking.booking_status?.toLowerCase() || 'submitted';
      switch (status) {
        case 'checked in':
          return { text: 'Checked In', color: 'green' };
        case 'checked out':
          return { text: 'Checked Out', color: 'gray' };
        default:
          return { text: 'Submitted', color: 'blue' };
      }
    }
    return { text: 'Draft', color: 'gray' };
  };

  return (
    <Box minH="100vh" bg="gray.50" py={6}>
      <Container maxW="container.xl">
        <VStack spacing={6} align="stretch">
          {/* Header */}
          <Box bg={bgColor} p={4} borderRadius="lg" shadow="sm">
            <Heading size="md" color="gray.700">
              Search Bookings
            </Heading>
          </Box>

          {/* Search Filters */}
          <Card bg={cardBg} shadow="sm">
            <CardBody p={6}>
              <VStack spacing={4} align="stretch">
                <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={4}>
                  <InputGroup>
                    <InputLeftElement pointerEvents="none">
                      <Icon as={FiSearch} color="gray.400" />
                    </InputLeftElement>
                    <Input
                      placeholder="Search by name..."
                      value={searchText}
                      onChange={(e) => setSearchText(e.target.value)}
                      bg="white"
                    />
                  </InputGroup>

                  <InputGroup>
                    <InputLeftElement pointerEvents="none">
                      <Icon as={FiCalendar} color="gray.400" />
                    </InputLeftElement>
                    <Input
                      type="date"
                      placeholder="From Date"
                      value={fromDate}
                      onChange={(e) => setFromDate(e.target.value)}
                      bg="white"
                    />
                  </InputGroup>

                  <InputGroup>
                    <InputLeftElement pointerEvents="none">
                      <Icon as={FiCalendar} color="gray.400" />
                    </InputLeftElement>
                    <Input
                      type="date"
                      placeholder="To Date"
                      value={toDate}
                      onChange={(e) => setToDate(e.target.value)}
                      bg="white"
                    />
                  </InputGroup>

                  <InputGroup>
                    <InputLeftElement pointerEvents="none">
                      <Icon as={FiUser} color="gray.400" />
                    </InputLeftElement>
                    <Input
                      placeholder="Devotee"
                      value={devotee}
                      onChange={(e) => setDevotee(e.target.value)}
                      bg="white"
                    />
                  </InputGroup>
                </SimpleGrid>

                <HStack spacing={4}>
                  <Select
                    value={sortField}
                    onChange={(e) => setSortField(e.target.value)}
                    bg="white"
                    maxW="200px"
                  >
                    <option value="creation">Created Date</option>
                    <option value="from_date">Check-in Date</option>
                    <option value="to_date">Check-out Date</option>
                    <option value="full_name">Name</option>
                  </Select>

                  <Select
                    value={sortOrder}
                    onChange={(e) => setSortOrder(e.target.value as 'asc' | 'desc')}
                    bg="white"
                    maxW="150px"
                  >
                    <option value="desc">Descending</option>
                    <option value="asc">Ascending</option>
                  </Select>

                  <IconButton
                    aria-label="Refresh"
                    icon={<FiRefreshCw />}
                    onClick={fetchBookings}
                    isLoading={loading}
                    colorScheme="blue"
                    variant="outline"
                  />
                </HStack>
              </VStack>
            </CardBody>
          </Card>

          {/* Bookings List */}
          {loading && bookings.length === 0 ? (
            <Box textAlign="center" py={12}>
              <Spinner size="xl" color="blue.500" />
              <Text mt={4} color="gray.600">
                Loading bookings...
              </Text>
            </Box>
          ) : bookings.length === 0 ? (
            <Box textAlign="center" py={12} bg={bgColor} borderRadius="lg" p={6}>
              <Text color="gray.600">No bookings found</Text>
            </Box>
          ) : (
            <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={4}>
              {bookings.map((booking) => (
                <Card
                  key={booking.name}
                  bg={cardBg}
                  shadow="sm"
                  borderRadius="lg"
                  cursor="pointer"
                  transition="all 0.2s"
                  _hover={{
                    shadow: 'md',
                    transform: 'translateY(-2px)',
                  }}
                  onClick={() => handleBookingClick(booking.name)}
                >
                  <CardBody p={4}>
                    <VStack align="stretch" spacing={3}>
                      <HStack justify="space-between">
                        <Text fontWeight="semibold" fontSize="md" noOfLines={1}>
                          {booking.full_name}
                        </Text>
                        {(() => {
                          const status = getBookingStatus(booking);
                          // Don't show badge for "Submitted" status (docstatus == 1 with default booking_status)
                          // Only show badge for Cancelled, Checked In, Checked Out, or Draft
                          if (status.text !== 'Submitted') {
                            return (
                              <Badge colorScheme={status.color} fontSize="xs">
                                {status.text}
                              </Badge>
                            );
                          }
                          return null;
                        })()}
                      </HStack>

                      <HStack spacing={2}>
                        <Icon as={FiCalendar} color="blue.500" boxSize={4} />
                        <Text fontSize="sm" color="gray.600">
                          {new Date(booking.from_date).toLocaleDateString()} -{' '}
                          {new Date(booking.to_date).toLocaleDateString()}
                        </Text>
                      </HStack>

                      {booking.devotee && (
                        <HStack spacing={2}>
                          <Icon as={FiUser} color="blue.500" boxSize={4} />
                          <Text fontSize="sm" color="gray.600">
                            {booking.devotee}
                          </Text>
                        </HStack>
                      )}

                      <HStack spacing={2}>
                        <Icon as={FiUsers} color="blue.500" boxSize={4} />
                        <Text fontSize="sm" color="gray.600">
                          {booking.total_person} guest{booking.total_person > 1 ? 's' : ''}
                        </Text>
                      </HStack>

                      <HStack spacing={2}>
                        <Icon as={FiDollarSign} color="green.500" boxSize={4} />
                        <Text fontSize="sm" fontWeight="medium" color="green.600">
                          ₹{booking.amount?.toLocaleString() || 0}
                        </Text>
                      </HStack>

                      <Button
                        leftIcon={<FiEye />}
                        size="sm"
                        colorScheme="blue"
                        variant="outline"
                        w="full"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleBookingClick(booking.name);
                        }}
                      >
                        View Details
                      </Button>
                    </VStack>
                  </CardBody>
                </Card>
              ))}
            </SimpleGrid>
          )}

          {/* Pagination */}
          {bookings.length > 0 && (
            <HStack justify="center" spacing={4}>
              <Button
                onClick={() => setPage(Math.max(0, page - 1))}
                isDisabled={page === 0}
                size="sm"
              >
                Previous
              </Button>
              <Text fontSize="sm" color="gray.600">
                Page {page + 1}
              </Text>
              <Button
                onClick={() => setPage(page + 1)}
                isDisabled={bookings.length < pageSize}
                size="sm"
              >
                Next
              </Button>
            </HStack>
          )}
        </VStack>
      </Container>

      {/* Booking Detail Modal */}
      {selectedBooking && (
        <BookingDetailModal
          isOpen={isDetailModalOpen}
          onClose={() => {
            setIsDetailModalOpen(false);
            setSelectedBooking(null);
          }}
          bookingId={selectedBooking}
          onBookingCancelled={() => {
            // Refresh bookings list after cancellation
            fetchBookings();
          }}
        />
      )}
    </Box>
  );
};

export default BookingsPage;


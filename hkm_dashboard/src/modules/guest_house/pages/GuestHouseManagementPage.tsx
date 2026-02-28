// Guest House Management Page
import React, { useState, useEffect, useRef, useCallback } from 'react';
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
  SimpleGrid,
  Card,
  CardBody,
  useColorModeValue,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  useDisclosure,
  Divider,
  IconButton,
  Input,
} from '@chakra-ui/react';
import {
  FiRefreshCw,
  FiCalendar,
  FiCheck,
  FiLock,
  FiUser,
  FiDollarSign,
  FiHome,
  FiChevronUp,
  FiChevronDown,
  FiLogOut,
  FiPlus,
  FiSearch,
} from 'react-icons/fi';
import { useNavigate } from 'react-router-dom';
import { guestHouseApi } from '../api/guestHouseApi';
import type { RoomsFloorWiseResponse, Room, Floor } from '../types';

const GuestHouseManagementPage: React.FC = () => {
  const navigate = useNavigate();
  const [data, setData] = useState<RoomsFloorWiseResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDate, setSelectedDate] = useState<string>(
    new Date().toISOString().split('T')[0]
  );
  const [selectedFloorIndex, setSelectedFloorIndex] = useState<number>(0);
  const [selectedRoom, setSelectedRoom] = useState<Room | null>(null);
  const [isSummaryExpanded, setIsSummaryExpanded] = useState<boolean>(true);
  const { isOpen, onOpen, onClose } = useDisclosure();
  const toast = useToast();
  const bgColor = useColorModeValue('white', 'gray.800');
  const cardBg = useColorModeValue('white', 'gray.700');
  const dateScrollRef = useRef<HTMLDivElement>(null);
  const dateInputRef = useRef<HTMLInputElement>(null);

  // Generate date options centered around selected date or today
  const generateDateOptions = useCallback((selectedDateStr?: string) => {
    const dates = new Set<string>();
    const today = new Date();
    
    // Use selected date as center point, or today if no selection
    const centerDate = selectedDateStr ? new Date(selectedDateStr) : today;
    
    // Add dates from -30 to +90 days from the center date
    for (let i = -30; i <= 90; i++) {
      const date = new Date(centerDate);
      date.setDate(centerDate.getDate() + i);
      dates.add(date.toISOString().split('T')[0]);
    }
    
    // Always include today's date
    dates.add(today.toISOString().split('T')[0]);
    
    // Always include the selected date if it's not already in the range
    if (selectedDateStr) {
      dates.add(selectedDateStr);
    }
    
    // Sort dates
    return Array.from(dates).sort();
  }, []);

  const [dateOptions, setDateOptions] = useState<string[]>(() => generateDateOptions());

  const fetchRooms = async (date?: string) => {
    try {
      setLoading(true);
      setError(null);

      const result = await guestHouseApi.getRoomsFloorWise(date);
      setData(result);
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to fetch room availability';
      setError(errorMessage);
      toast({
        title: 'Error',
        description: errorMessage,
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRooms(selectedDate);
  }, [selectedDate]);

  useEffect(() => {
    // Reset to first floor when data changes
    if (data?.floors && data.floors.length > 0) {
      setSelectedFloorIndex(0);
    }
  }, [data]);

  useEffect(() => {
    // Update date options centered around selected date
    const newDateOptions = generateDateOptions(selectedDate);
    setDateOptions(newDateOptions);
  }, [selectedDate, generateDateOptions]);

  useEffect(() => {
    // Scroll to selected date in date selector after a short delay to ensure DOM is updated
    const timer = setTimeout(() => {
      if (dateScrollRef.current) {
        const selectedElement = dateScrollRef.current.querySelector(
          `[data-date="${selectedDate}"]`
        );
        if (selectedElement) {
          selectedElement.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
        }
      }
    }, 100);
    
    return () => clearTimeout(timer);
  }, [selectedDate, dateOptions]);

  const handleCalendarIconClick = () => {
    if (dateInputRef.current) {
      if (typeof dateInputRef.current.showPicker === 'function') {
        dateInputRef.current.showPicker();
      } else {
        dateInputRef.current.click();
      }
    }
  };

  const handleDateSelect = (date: string) => {
    setSelectedDate(date);
  };

  const handleRefresh = () => {
    fetchRooms(selectedDate);
  };

  const handleRoomClick = (room: Room) => {
    setSelectedRoom(room);
    onOpen();
  };

  const getStatusColor = (status: Room['status']): string => {
    switch (status) {
      case 'available':
        return 'green';
      case 'booked':
        return 'red';
      case 'checking_in_today':
        return 'blue';
      case 'checking_out_today':
        return 'orange';
      default:
        return 'gray';
    }
  };

  const formatDateCard = (dateStr: string) => {
    const date = new Date(dateStr);
    const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const monthNames = [
      'Jan',
      'Feb',
      'Mar',
      'Apr',
      'May',
      'Jun',
      'Jul',
      'Aug',
      'Sep',
      'Oct',
      'Nov',
      'Dec',
    ];
    return {
      day: dayNames[date.getDay()],
      month: monthNames[date.getMonth()],
      dayNum: date.getDate(),
    };
  };

  const RoomCard: React.FC<{ room: Room }> = ({ room }) => {
    const isAvailable = room.status === 'available';
    const isBooked = room.status === 'booked';

    return (
      <Card
        bg={cardBg}
        shadow="sm"
        borderRadius="lg"
        borderWidth="1px"
        cursor="pointer"
        transition="all 0.2s"
        _hover={{
          shadow: 'md',
          transform: 'translateY(-2px)',
        }}
        onClick={() => handleRoomClick(room)}
      >
        <CardBody p={3}>
          <VStack align="stretch" spacing={2}>
            {/* Status Icon and Room Number */}
            <Flex justify="space-between" align="center">
              <HStack spacing={2}>
                <Box
                  w={8}
                  h={8}
                  borderRadius="full"
                  bg={isAvailable ? 'blue.100' : 'red.100'}
                  display="flex"
                  alignItems="center"
                  justifyContent="center"
                >
                  <Icon
                    as={isAvailable ? FiCheck : FiLock}
                    color={isAvailable ? 'blue.600' : 'red.600'}
                    boxSize={4}
                  />
                </Box>
                <Text fontSize="md" fontWeight="semibold">
                  {room.room_details}
                </Text>
              </HStack>
            </Flex>

            {/* Status Text */}
            <Text
              fontSize="sm"
              color={isAvailable ? 'blue.600' : 'red.600'}
              fontWeight="medium"
            >
              {isAvailable ? 'Available' : 'Booked'}
            </Text>

            {/* Guest Name if booked */}
            {room.booking && (
              <Text fontSize="xs" color="gray.600" noOfLines={1}>
                {room.booking.guest_name}
              </Text>
            )}
          </VStack>
        </CardBody>
      </Card>
    );
  };

  if (loading && !data) {
    return (
      <Box minH="100vh" bg="gray.50" py={12}>
        <Container maxW="container.xl">
          <Flex justify="center" align="center" minH="60vh">
            <VStack spacing={4}>
              <Spinner size="xl" color="blue.500" />
              <Text color="gray.600">Loading room availability...</Text>
            </VStack>
          </Flex>
        </Container>
      </Box>
    );
  }

  if (error && !data) {
    return (
      <Box minH="100vh" bg="gray.50" py={12}>
        <Container maxW="container.xl">
          <VStack spacing={4} align="stretch">
            <Box p={6} bg="red.50" borderRadius="lg" borderWidth="1px" borderColor="red.200">
              <Text color="red.800" fontWeight="medium">
                Error: {error}
              </Text>
            </Box>
            <Button onClick={handleRefresh} colorScheme="blue" leftIcon={<FiRefreshCw />}>
              Retry
            </Button>
          </VStack>
        </Container>
      </Box>
    );
  }

  return (
    <Box minH="100vh" bg="gray.50" py={6}>
      <Container maxW="container.xl">
        <VStack spacing={4} align="stretch">
          {/* Header */}
          <Box bg={bgColor} p={4} borderRadius="lg" shadow="sm">
            <Flex justify="space-between" align="center" flexWrap="wrap" gap={3}>
              <VStack align="start" spacing={0}>
                <Heading size="md" color="gray.700">
                  Room Availability
                </Heading>
              </VStack>
              <HStack spacing={2}>
                <Button
                  leftIcon={<FiSearch />}
                  colorScheme="blue"
                  variant="outline"
                  size="sm"
                  onClick={() => navigate('/guest-house/bookings')}
                >
                  Search Bookings
                </Button>
                <IconButton
                  aria-label="Refresh"
                  icon={<FiRefreshCw />}
                  onClick={handleRefresh}
                  colorScheme="blue"
                  variant="ghost"
                  isLoading={loading}
                />
              </HStack>
            </Flex>
          </Box>

          {/* Date Selector */}
          <Box bg={bgColor} p={4} borderRadius="lg" shadow="sm">
            <HStack justify="space-between" mb={3}>
              <Text fontSize="sm" fontWeight="medium" color="gray.700">
                Select Date
              </Text>
              <Box position="relative">
                <Input
                  ref={dateInputRef}
                  type="date"
                  value={selectedDate}
                  onChange={(e) => {
                    if (e.target.value) {
                      handleDateSelect(e.target.value);
                    }
                  }}
                  position="absolute"
                  opacity={0}
                  width="0"
                  height="0"
                  pointerEvents="none"
                />
                <IconButton
                  aria-label="Open calendar"
                  icon={<FiCalendar />}
                  onClick={handleCalendarIconClick}
                  colorScheme="blue"
                  variant="ghost"
                  size="sm"
                />
              </Box>
            </HStack>
            <Box
              ref={dateScrollRef}
              overflowX="auto"
              css={{
                '&::-webkit-scrollbar': {
                  height: '4px',
                },
                '&::-webkit-scrollbar-track': {
                  background: '#f1f1f1',
                },
                '&::-webkit-scrollbar-thumb': {
                  background: '#888',
                  borderRadius: '2px',
                },
              }}
            >
              <HStack spacing={3} pb={2}>
                {dateOptions.map((date) => {
                  const formatted = formatDateCard(date);
                  const isSelected = date === selectedDate;
                  return (
                    <Card
                      key={date}
                      data-date={date}
                      bg={isSelected ? 'blue.600' : 'white'}
                      color={isSelected ? 'white' : 'gray.700'}
                      shadow="sm"
                      borderRadius="md"
                      borderWidth="1px"
                      borderColor={isSelected ? 'blue.600' : 'gray.200'}
                      cursor="pointer"
                      minW="80px"
                      transition="all 0.2s"
                      _hover={{
                        shadow: 'md',
                        transform: 'translateY(-2px)',
                      }}
                      onClick={() => handleDateSelect(date)}
                    >
                      <CardBody p={3}>
                        <VStack spacing={0}>
                          <Text fontSize="xs" fontWeight="medium">
                            {formatted.day}
                          </Text>
                          <Text fontSize="xs" color={isSelected ? 'white' : 'gray.500'}>
                            {formatted.month}
                          </Text>
                          <Text fontSize="lg" fontWeight="bold">
                            {formatted.dayNum}
                          </Text>
                        </VStack>
                      </CardBody>
                    </Card>
                  );
                })}
              </HStack>
            </Box>
          </Box>

          {/* Room Availability Summary */}
          {data?.summary && (
            <Box bg={bgColor} p={4} borderRadius="lg" shadow="sm">
              <Box
                as="button"
                w="full"
                onClick={() => setIsSummaryExpanded(!isSummaryExpanded)}
                cursor="pointer"
              >
                <HStack justify="space-between">
                  <HStack spacing={2}>
                    <Icon as={FiHome} color="blue.500" boxSize={5} />
                    <Text fontSize="sm" fontWeight="semibold" color="gray.700">
                      Room Availability Summary
                    </Text>
                  </HStack>
                  <Icon
                    as={isSummaryExpanded ? FiChevronUp : FiChevronDown}
                    color="gray.500"
                    boxSize={5}
                  />
                </HStack>
              </Box>

              {isSummaryExpanded && (
                <SimpleGrid columns={2} spacing={4} mt={4}>
                  {/* Total Rooms */}
                  <Box>
                    <HStack spacing={2} mb={2}>
                      <Icon as={FiHome} color="blue.500" boxSize={4} />
                      <Text fontSize="xs" color="gray.600" fontWeight="medium">
                        Total
                      </Text>
                    </HStack>
                    <Text fontSize="2xl" fontWeight="bold" color="blue.600">
                      {data.summary.total_rooms}
                    </Text>
                  </Box>

                  {/* Booked Rooms */}
                  <Box>
                    <HStack spacing={2} mb={2}>
                      <Icon as={FiLock} color="red.500" boxSize={4} />
                      <Text fontSize="xs" color="gray.600" fontWeight="medium">
                        Booked
                      </Text>
                    </HStack>
                    <Text fontSize="2xl" fontWeight="bold" color="red.600">
                      {data.summary.booked_rooms}
                    </Text>
                  </Box>

                  {/* Available Rooms */}
                  <Box>
                    <HStack spacing={2} mb={2}>
                      <Icon as={FiCheck} color="blue.500" boxSize={4} />
                      <Text fontSize="xs" color="gray.600" fontWeight="medium">
                        Available
                      </Text>
                    </HStack>
                    <Text fontSize="2xl" fontWeight="bold" color="blue.600">
                      {data.summary.available_rooms}
                    </Text>
                  </Box>

                  {/* Checking Out Today */}
                  <Box>
                    <HStack spacing={2} mb={2}>
                      <Icon as={FiLogOut} color="blue.500" boxSize={4} />
                      <Text fontSize="xs" color="gray.600" fontWeight="medium">
                        Check-out Today
                      </Text>
                    </HStack>
                    <Text fontSize="2xl" fontWeight="bold" color="blue.600">
                      {data.summary.checking_out_today}
                    </Text>
                  </Box>

                  {/* Checking In Today - if exists */}
                  {data.summary.checking_in_today !== undefined && (
                    <Box>
                      <HStack spacing={2} mb={2}>
                        <Icon as={FiCalendar} color="blue.500" boxSize={4} />
                        <Text fontSize="xs" color="gray.600" fontWeight="medium">
                          Check-in Today
                        </Text>
                      </HStack>
                      <Text fontSize="2xl" fontWeight="bold" color="blue.600">
                        {data.summary.checking_in_today}
                      </Text>
                    </Box>
                  )}
                </SimpleGrid>
              )}
            </Box>
          )}

          {/* Floors with Tabs */}
          {data?.floors && data.floors.length > 0 ? (
            <Box bg={bgColor} borderRadius="lg" shadow="sm" p={4}>
              <Tabs
                index={selectedFloorIndex}
                onChange={setSelectedFloorIndex}
                colorScheme="blue"
                variant="enclosed"
              >
                <TabList mb={4} overflowX="auto">
                  {data.floors.map((floor) => (
                    <Tab key={floor.floor} fontSize="sm" px={4} py={2}>
                      Floor {floor.floor}
                      <Badge ml={2} colorScheme="blue" fontSize="2xs">
                        {floor.rooms.length}
                      </Badge>
                    </Tab>
                  ))}
                </TabList>

                <TabPanels>
                  {data.floors.map((floor) => (
                    <TabPanel key={floor.floor} px={0}>
                      <VStack align="stretch" spacing={3}>
                        <Text fontSize="sm" color="gray.600">
                          {floor.rooms.length} rooms
                        </Text>
                        <SimpleGrid
                          columns={{ base: 2, sm: 3, md: 4, lg: 5, xl: 6 }}
                          spacing={3}
                        >
                          {floor.rooms.map((room) => (
                            <RoomCard key={room.room_id} room={room} />
                          ))}
                        </SimpleGrid>
                      </VStack>
                    </TabPanel>
                  ))}
                </TabPanels>
              </Tabs>
            </Box>
          ) : (
            <Box p={6} bg={bgColor} borderRadius="lg" textAlign="center">
              <Text color="gray.600">No rooms found</Text>
            </Box>
          )}
        </VStack>
      </Container>

      {/* Booking Details Modal */}
      <Modal isOpen={isOpen} onClose={onClose} size="md" isCentered>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>
            <HStack justify="space-between">
              <HStack>
                <Text>Room {selectedRoom?.room_details}</Text>
                {selectedRoom && (
                  <Badge colorScheme="blue" fontSize="xs">
                    Floor {selectedRoom.floor}
                  </Badge>
                )}
              </HStack>
            </HStack>
            <Text fontSize="sm" fontWeight="normal" color="gray.600" mt={1}>
              Booking Details
            </Text>
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            {selectedRoom ? (
              <VStack align="stretch" spacing={4}>
                {selectedRoom.booking ? (
                  <>
                    <Box>
                      <Text fontSize="xs" color="gray.500" mb={1}>
                        Guest Name
                      </Text>
                      <HStack>
                        <Icon as={FiUser} color="blue.500" boxSize={4} />
                        <Text fontSize="sm" fontWeight="medium">
                          {selectedRoom.booking.guest_name}
                        </Text>
                      </HStack>
                    </Box>

                    {selectedRoom.booking.devotee && (
                      <Box>
                        <Text fontSize="xs" color="gray.500" mb={1}>
                          Devotee
                        </Text>
                        <Text fontSize="sm">{selectedRoom.booking.devotee}</Text>
                      </Box>
                    )}

                    <Divider />

                    <Box>
                      <Text fontSize="xs" color="gray.500" mb={1}>
                        Check-in
                      </Text>
                      <HStack>
                        <Icon as={FiCalendar} color="blue.500" boxSize={4} />
                        <Text fontSize="sm">
                          {new Date(selectedRoom.booking.check_in_date).toLocaleDateString(
                            'en-GB',
                            {
                              day: '2-digit',
                              month: 'short',
                              year: '2-digit',
                            }
                          )}{' '}
                          at 12:00 PM
                        </Text>
                      </HStack>
                    </Box>

                    <Box>
                      <Text fontSize="xs" color="gray.500" mb={1}>
                        Check-out
                      </Text>
                      <HStack>
                        <Icon as={FiCalendar} color="blue.500" boxSize={4} />
                        <Text fontSize="sm">
                          {new Date(selectedRoom.booking.check_out_date).toLocaleDateString(
                            'en-GB',
                            {
                              day: '2-digit',
                              month: 'short',
                              year: '2-digit',
                            }
                          )}{' '}
                          at 10:00 AM
                        </Text>
                      </HStack>
                    </Box>

                    <Divider />

                    <Box>
                      <Text fontSize="xs" color="gray.500" mb={1}>
                        Status
                      </Text>
                      <Badge
                        colorScheme={getStatusColor(selectedRoom.status)}
                        fontSize="xs"
                        px={2}
                        py={1}
                      >
                        {selectedRoom.status.replace(/_/g, ' ').toUpperCase()}
                      </Badge>
                    </Box>

                    <Box>
                      <Text fontSize="xs" color="gray.500" mb={1}>
                        Guests
                      </Text>
                      <Text fontSize="sm">
                        {selectedRoom.booking.total_person} person
                        {selectedRoom.booking.total_person > 1 ? 's' : ''}
                      </Text>
                    </Box>

                    {selectedRoom.booking.amount > 0 && (
                      <Box>
                        <Text fontSize="xs" color="gray.500" mb={1}>
                          Amount
                        </Text>
                        <HStack>
                          <Icon as={FiDollarSign} color="green.500" boxSize={4} />
                          <Text fontSize="sm" fontWeight="semibold">
                            ₹{selectedRoom.booking.amount.toLocaleString()}
                          </Text>
                        </HStack>
                      </Box>
                    )}

                    <Divider />

                    <Box>
                      <Text fontSize="xs" color="gray.500" mb={1}>
                        Availability Note
                      </Text>
                      <Text fontSize="sm" color="gray.700">
                        {selectedRoom.availability_note}
                      </Text>
                    </Box>

                    {selectedRoom.available_from_date && (
                      <Box>
                        <Text fontSize="xs" color="gray.500" mb={1}>
                          Available From
                        </Text>
                        <Text fontSize="sm">
                          {new Date(selectedRoom.available_from_date).toLocaleDateString(
                            'en-GB',
                            {
                              day: '2-digit',
                              month: 'short',
                              year: 'numeric',
                            }
                          )}
                        </Text>
                      </Box>
                    )}
                  </>
                ) : (
                  <VStack spacing={3}>
                    <Text fontSize="sm" color="gray.600">
                      {selectedRoom.availability_note}
                    </Text>
                    {selectedRoom.available_from_date && (
                      <Box w="full">
                        <Text fontSize="xs" color="gray.500" mb={1}>
                          Available From
                        </Text>
                        <Text fontSize="sm">
                          {new Date(selectedRoom.available_from_date).toLocaleDateString('en-GB', {
                            day: '2-digit',
                            month: 'short',
                            year: 'numeric',
                          })}
                        </Text>
                      </Box>
                    )}
                  </VStack>
                )}
              </VStack>
            ) : null}
          </ModalBody>
        </ModalContent>
      </Modal>

      {/* Floating Action Button */}
      <Button
        position="fixed"
        bottom={6}
        right={6}
        leftIcon={<FiPlus />}
        colorScheme="blue"
        size="lg"
        borderRadius="full"
        boxShadow="lg"
        onClick={() => navigate('/guest-house/new-booking')}
        zIndex={1000}
      >
        New Booking
      </Button>
    </Box>
  );
};

export default GuestHouseManagementPage;

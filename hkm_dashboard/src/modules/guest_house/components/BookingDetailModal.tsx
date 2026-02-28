// Booking Detail Modal Component
import React, { useState, useEffect } from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  VStack,
  HStack,
  Text,
  Badge,
  Box,
  Icon,
  useColorModeValue,
  Divider,
  SimpleGrid,
  Image,
  Spinner,
  useToast,
  Button,
} from '@chakra-ui/react';
import {
  FiUser,
  FiCalendar,
  FiDollarSign,
  FiUsers,
  FiHome,
  FiMapPin,
  FiX,
  FiXCircle,
} from 'react-icons/fi';
import { guestHouseApi } from '../api/guestHouseApi';

interface BookingDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  bookingId: string;
}

const BookingDetailModal: React.FC<BookingDetailModalProps> = ({
  isOpen,
  onClose,
  bookingId,
  onBookingCancelled,
}) => {
  const [booking, setBooking] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [cancelling, setCancelling] = useState<boolean>(false);
  const toast = useToast();
  const bgColor = useColorModeValue('white', 'gray.800');

  useEffect(() => {
    if (isOpen && bookingId) {
      fetchBookingDetails();
    }
  }, [isOpen, bookingId]);

  const fetchBookingDetails = async () => {
    setLoading(true);
    try {
      const result = await guestHouseApi.getBookingDetailedInfo(bookingId);
      setBooking(result);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to fetch booking details',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  const getBookingStatus = (booking: any) => {
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

  const formatDate = (dateStr: string) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString('en-GB', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });
  };

  const formatDateTime = (dateStr: string, timeStr?: string) => {
    if (!dateStr) return 'N/A';
    const date = new Date(dateStr);
    let formatted = formatDate(dateStr);
    if (timeStr) {
      formatted += ` at ${timeStr}`;
    }
    return formatted;
  };

  const handleCancelBooking = async () => {
    if (!window.confirm('Are you sure you want to cancel this booking?')) {
      return;
    }

    setCancelling(true);
    try {
      await guestHouseApi.cancelBooking(bookingId);
      toast({
        title: 'Success',
        description: 'Booking cancelled successfully',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
      
      // Refresh booking details
      await fetchBookingDetails();
      
      // Notify parent component
      if (onBookingCancelled) {
        onBookingCancelled();
      }
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to cancel booking',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setCancelling(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="xl" isCentered>
      <ModalOverlay />
      <ModalContent maxH="90vh" display="flex" flexDirection="column">
        <ModalHeader>
          <HStack justify="space-between">
            <Text>Booking Details</Text>
            {booking && (() => {
              const status = getBookingStatus(booking);
              return (
                <Badge colorScheme={status.color} fontSize="sm">
                  {status.text}
                </Badge>
              );
            })()}
          </HStack>
        </ModalHeader>
        <ModalCloseButton />
        <ModalBody flex="1" overflowY="auto" pb={6}>
          {loading ? (
            <Box textAlign="center" py={8}>
              <Spinner size="xl" color="blue.500" />
              <Text mt={4} color="gray.600">
                Loading booking details...
              </Text>
            </Box>
          ) : booking ? (
            <VStack spacing={4} align="stretch">
              {/* Guest Information */}
              <Box>
                <Text fontSize="sm" fontWeight="semibold" color="gray.700" mb={3}>
                  Guest Information
                </Text>
                <VStack spacing={3} align="stretch">
                  <HStack>
                    <Icon as={FiUser} color="blue.500" boxSize={4} />
                    <VStack align="start" spacing={0}>
                      <Text fontSize="xs" color="gray.500">
                        Full Name
                      </Text>
                      <Text fontSize="sm" fontWeight="medium">
                        {booking.full_name}
                      </Text>
                    </VStack>
                  </HStack>

                  {booking.devotee && (
                    <HStack>
                      <Icon as={FiUser} color="blue.500" boxSize={4} />
                      <VStack align="start" spacing={0}>
                        <Text fontSize="xs" color="gray.500">
                          Devotee
                        </Text>
                        <Text fontSize="sm" fontWeight="medium">
                          {booking.devotee}
                        </Text>
                      </VStack>
                    </HStack>
                  )}

                  {booking.address && (
                    <HStack>
                      <Icon as={FiMapPin} color="blue.500" boxSize={4} />
                      <VStack align="start" spacing={0}>
                        <Text fontSize="xs" color="gray.500">
                          Address
                        </Text>
                        <Text fontSize="sm">{booking.address}</Text>
                      </VStack>
                    </HStack>
                  )}

                  <HStack>
                    <Icon as={FiUsers} color="blue.500" boxSize={4} />
                    <VStack align="start" spacing={0}>
                      <Text fontSize="xs" color="gray.500">
                        Total Persons
                      </Text>
                      <Text fontSize="sm">
                        {booking.total_person} person{booking.total_person > 1 ? 's' : ''}
                      </Text>
                    </VStack>
                  </HStack>

                  {booking.guest_type && (
                    <HStack>
                      <Icon as={FiUser} color="blue.500" boxSize={4} />
                      <VStack align="start" spacing={0}>
                        <Text fontSize="xs" color="gray.500">
                          Guest Type
                        </Text>
                        <Text fontSize="sm">{booking.guest_type}</Text>
                      </VStack>
                    </HStack>
                  )}
                </VStack>
              </Box>

              <Divider />

              {/* Booking Dates */}
              <Box>
                <Text fontSize="sm" fontWeight="semibold" color="gray.700" mb={3}>
                  Booking Dates
                </Text>
                <VStack spacing={3} align="stretch">
                  <HStack>
                    <Icon as={FiCalendar} color="blue.500" boxSize={4} />
                    <VStack align="start" spacing={0}>
                      <Text fontSize="xs" color="gray.500">
                        Check-in
                      </Text>
                      <Text fontSize="sm" fontWeight="medium">
                        {formatDateTime(booking.from_date, '12:00 PM')}
                      </Text>
                    </VStack>
                  </HStack>

                  <HStack>
                    <Icon as={FiCalendar} color="blue.500" boxSize={4} />
                    <VStack align="start" spacing={0}>
                      <Text fontSize="xs" color="gray.500">
                        Check-out
                      </Text>
                      <Text fontSize="sm" fontWeight="medium">
                        {formatDateTime(booking.to_date, '10:00 AM')}
                      </Text>
                    </VStack>
                  </HStack>

                  {booking.actual_check_in && (
                    <HStack>
                      <Icon as={FiCalendar} color="green.500" boxSize={4} />
                      <VStack align="start" spacing={0}>
                        <Text fontSize="xs" color="gray.500">
                          Actual Check-in
                        </Text>
                        <Text fontSize="sm">{formatDate(booking.actual_check_in)}</Text>
                      </VStack>
                    </HStack>
                  )}

                  {booking.actual_check_out && (
                    <HStack>
                      <Icon as={FiCalendar} color="green.500" boxSize={4} />
                      <VStack align="start" spacing={0}>
                        <Text fontSize="xs" color="gray.500">
                          Actual Check-out
                        </Text>
                        <Text fontSize="sm">{formatDate(booking.actual_check_out)}</Text>
                      </VStack>
                    </HStack>
                  )}
                </VStack>
              </Box>

              <Divider />

              {/* Rooms */}
              {booking.room_details && booking.room_details.length > 0 && (
                <Box>
                  <Text fontSize="sm" fontWeight="semibold" color="gray.700" mb={3}>
                    Rooms ({booking.room_details.length})
                  </Text>
                  <VStack spacing={2} align="stretch">
                    {booking.room_details.map((room: any, index: number) => (
                      <Box
                        key={index}
                        p={3}
                        bg="gray.50"
                        borderRadius="md"
                        borderWidth="1px"
                      >
                        <HStack justify="space-between">
                          <HStack>
                            <Icon as={FiHome} color="blue.500" boxSize={4} />
                            <VStack align="start" spacing={0}>
                              <Text fontSize="sm" fontWeight="medium">
                                {room.room || room.room_number || `Room ${index + 1}`}
                              </Text>
                              {room.room_type && (
                                <Text fontSize="xs" color="gray.600">
                                  {room.room_type}
                                </Text>
                              )}
                            </VStack>
                          </HStack>
                          {room.amount && (
                            <Text fontSize="sm" fontWeight="medium" color="green.600">
                              ₹{room.amount.toLocaleString()}
                            </Text>
                          )}
                        </HStack>
                      </Box>
                    ))}
                  </VStack>
                </Box>
              )}

              <Divider />

              {/* Amount */}
              {booking.amount && (
                <Box>
                  <HStack justify="space-between">
                    <HStack>
                      <Icon as={FiDollarSign} color="green.500" boxSize={5} />
                      <Text fontSize="sm" fontWeight="semibold" color="gray.700">
                        Total Amount
                      </Text>
                    </HStack>
                    <Text fontSize="lg" fontWeight="bold" color="green.600">
                      ₹{booking.amount.toLocaleString()}
                    </Text>
                  </HStack>
                </Box>
              )}

              {/* Images */}
              {booking.image_urls && booking.image_urls.length > 0 && (
                <>
                  <Divider />
                  <Box>
                    <Text fontSize="sm" fontWeight="semibold" color="gray.700" mb={3}>
                      Attachments ({booking.image_urls.length})
                    </Text>
                    <SimpleGrid columns={3} spacing={3}>
                      {booking.image_urls.map((url: string, index: number) => (
                        <Box
                          key={index}
                          position="relative"
                          borderRadius="md"
                          overflow="hidden"
                          borderWidth="1px"
                        >
                          <Image
                            src={url}
                            alt={`Attachment ${index + 1}`}
                            objectFit="cover"
                            h="100px"
                            w="100%"
                            cursor="pointer"
                            onClick={() => window.open(url, '_blank')}
                          />
                        </Box>
                      ))}
                    </SimpleGrid>
                  </Box>
                </>
              )}

              {/* Booking ID */}
              <Box>
                <Text fontSize="xs" color="gray.500">
                  Booking ID: {booking.name}
                </Text>
                <Text fontSize="xs" color="gray.500">
                  Created: {formatDate(booking.creation)}
                </Text>
              </Box>

              {/* Cancel Booking Button */}
              {booking.docstatus === 1 && booking.booking_status?.toLowerCase() !== 'cancelled' && (
                <>
                  <Divider />
                  <Button
                    leftIcon={<FiXCircle />}
                    colorScheme="red"
                    variant="outline"
                    w="full"
                    onClick={handleCancelBooking}
                    isLoading={cancelling}
                    loadingText="Cancelling..."
                  >
                    Cancel Booking
                  </Button>
                </>
              )}
            </VStack>
          ) : (
            <Box textAlign="center" py={8}>
              <Text color="gray.600">No booking details available</Text>
            </Box>
          )}
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};

export default BookingDetailModal;


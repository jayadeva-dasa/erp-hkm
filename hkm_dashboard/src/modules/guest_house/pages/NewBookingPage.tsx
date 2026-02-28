// New Booking Page
import React, { useState, useEffect } from 'react';
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
  Card,
  CardBody,
  useColorModeValue,
  Input,
  InputGroup,
  InputLeftElement,
  Textarea,
  Select,
  NumberInput,
  NumberInputField,
  SimpleGrid,
  Image,
  IconButton,
  Divider,
} from '@chakra-ui/react';
import {
  FiCalendar,
  FiUser,
  FiMapPin,
  FiUsers,
  FiCheck,
  FiX,
  FiCamera,
  FiHome,
  FiEdit2,
  FiTrash2,
} from 'react-icons/fi';
import { useNavigate } from 'react-router-dom';
import { guestHouseApi, CreateBookingData, BookingRoomDetail } from '../api/guestHouseApi';
import RoomSelectionModal from '../components/RoomSelectionModal';
import type { Room } from '../types';

interface SelectedRoom extends Room {
  amount: number;
  room_type?: string;
}

const NewBookingPage: React.FC = () => {
  const navigate = useNavigate();
  const toast = useToast();
  const bgColor = useColorModeValue('white', 'gray.800');
  const cardBg = useColorModeValue('white', 'gray.700');

  // Form state
  const [fromDate, setFromDate] = useState<string>('');
  const [toDate, setToDate] = useState<string>('');
  const [devotee, setDevotee] = useState<string>('');
  const [devoteeSearchTerm, setDevoteeSearchTerm] = useState<string>('');
  const [devotees, setDevotees] = useState<Array<{ name: string; full_name: string }>>([]);
  const [fullName, setFullName] = useState<string>('');
  const [address, setAddress] = useState<string>('');
  const [totalPerson, setTotalPerson] = useState<number>(1);
  const [guestType, setGuestType] = useState<string>('');
  const [roomTypes, setRoomTypes] = useState<Array<{ room_type: string; guest_type: string; amount: number }>>([]);
  const [selectedRooms, setSelectedRooms] = useState<SelectedRoom[]>([]);
  const [images, setImages] = useState<File[]>([]);
  const [imagePreviews, setImagePreviews] = useState<string[]>([]);

  // UI state
  const [isRoomModalOpen, setIsRoomModalOpen] = useState<boolean>(false);
  const [availableRoomsCount, setAvailableRoomsCount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(false);
  const [searchingDevotees, setSearchingDevotees] = useState<boolean>(false);

  // Initialize dates (default to today and tomorrow)
  useEffect(() => {
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    setFromDate(today.toISOString().split('T')[0]);
    setToDate(tomorrow.toISOString().split('T')[0]);
  }, []);

  // Fetch room types
  useEffect(() => {
    const fetchRoomTypes = async () => {
      try {
        const types = await guestHouseApi.getRoomTypes();
        setRoomTypes(types);
        if (types.length > 0 && !guestType) {
          setGuestType(types[0].guest_type);
        }
      } catch (error: any) {
        console.error('Error fetching room types:', error);
      }
    };
    fetchRoomTypes();
  }, []);

  // Fetch available rooms count when dates change
  useEffect(() => {
    const fetchAvailableRooms = async () => {
      if (fromDate && toDate && fromDate < toDate) {
        try {
          const result = await guestHouseApi.getAvailableRooms(fromDate, toDate);
          setAvailableRoomsCount(result.total_available || 0);
        } catch (error: any) {
          console.error('Error fetching available rooms:', error);
          setAvailableRoomsCount(0);
        }
      }
    };
    fetchAvailableRooms();
  }, [fromDate, toDate]);

  // Search devotees
  useEffect(() => {
    const searchDevotees = async () => {
      if (devoteeSearchTerm.length >= 2) {
        setSearchingDevotees(true);
        try {
          const results = await guestHouseApi.searchDevotees(devoteeSearchTerm);
          setDevotees(results || []);
        } catch (error: any) {
          console.error('Error searching devotees:', error);
        } finally {
          setSearchingDevotees(false);
        }
      } else {
        setDevotees([]);
      }
    };

    const timer = setTimeout(searchDevotees, 300);
    return () => clearTimeout(timer);
  }, [devoteeSearchTerm]);

  const handleDevoteeSelect = (devoteeName: string, devoteeFullName: string) => {
    setDevotee(devoteeName);
    // Don't auto-fill full name - let user enter it separately
    setDevoteeSearchTerm('');
    setDevotees([]);
  };

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length + images.length > 5) {
      toast({
        title: 'Error',
        description: 'Maximum 5 images allowed',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    const newImages = [...images, ...files];
    setImages(newImages);

    // Create previews
    const newPreviews = files.map((file) => URL.createObjectURL(file));
    setImagePreviews([...imagePreviews, ...newPreviews]);
  };

  const handleRemoveImage = (index: number) => {
    const newImages = images.filter((_, i) => i !== index);
    const newPreviews = imagePreviews.filter((_, i) => i !== index);
    setImages(newImages);
    setImagePreviews(newPreviews);
  };

  const handleRoomSelect = (rooms: SelectedRoom[]) => {
    setSelectedRooms(rooms);
    setIsRoomModalOpen(false);
  };

  const calculateTotalAmount = () => {
    return selectedRooms.reduce((sum, room) => sum + (room.amount || 0), 0);
  };

  const handleSubmit = async () => {
    // Validation
    if (!fromDate || !toDate) {
      toast({
        title: 'Error',
        description: 'Please select check-in and check-out dates',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    if (!fullName) {
      toast({
        title: 'Error',
        description: 'Please enter full name',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    if (!address) {
      toast({
        title: 'Error',
        description: 'Please enter address',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    if (selectedRooms.length === 0) {
      toast({
        title: 'Error',
        description: 'Please select at least one room',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    setLoading(true);

    try {
      const bookingData: CreateBookingData = {
        from_date: fromDate,
        to_date: toDate,
        full_name: fullName,
        address: address,
        total_person: totalPerson,
        guest_type: guestType,
        devotee: devotee || undefined,
        amount: calculateTotalAmount(),
        room_details: selectedRooms.map((room) => ({
          room: room.room_id,
          amount: room.amount || 0,
        })),
      };

      const bookingId = await guestHouseApi.createBooking(bookingData);

      // Upload images if any
      if (images.length > 0) {
        try {
          await guestHouseApi.uploadBookingImages(bookingId, images);
        } catch (error: any) {
          console.error('Error uploading images:', error);
          toast({
            title: 'Warning',
            description: 'Booking created but image upload failed',
            status: 'warning',
            duration: 5000,
            isClosable: true,
          });
        }
      }

      toast({
        title: 'Success',
        description: 'Booking created successfully',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });

      // Navigate back to guest house management
      navigate('/guest-house');
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to create booking',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box minH="100vh" bg="gray.50" py={6}>
      <Container maxW="container.md">
        <VStack spacing={6} align="stretch">
          {/* Header */}
          <Box bg={bgColor} p={4} borderRadius="lg" shadow="sm">
            <Heading size="md" color="gray.700">
              New Booking
            </Heading>
          </Box>

          {/* Booking Dates */}
          <Card bg={cardBg} shadow="sm">
            <CardBody p={6}>
              <Heading size="sm" mb={4} color="gray.700">
                Booking Dates
              </Heading>
              <SimpleGrid columns={2} spacing={4} mb={4}>
                <Box>
                  <InputGroup>
                    <InputLeftElement pointerEvents="none">
                      <Icon as={FiCalendar} color="blue.500" />
                    </InputLeftElement>
                    <Input
                      type="date"
                      value={fromDate}
                      onChange={(e) => setFromDate(e.target.value)}
                      placeholder="Check-in"
                      bg="white"
                    />
                  </InputGroup>
                  <Text fontSize="xs" color="gray.600" mt={1}>
                    Check-in
                  </Text>
                </Box>
                <Box>
                  <InputGroup>
                    <InputLeftElement pointerEvents="none">
                      <Icon as={FiCalendar} color="blue.500" />
                    </InputLeftElement>
                    <Input
                      type="date"
                      value={toDate}
                      onChange={(e) => setToDate(e.target.value)}
                      placeholder="Check-out"
                      bg="white"
                    />
                  </InputGroup>
                  <Text fontSize="xs" color="gray.600" mt={1}>
                    Check-out
                  </Text>
                </Box>
              </SimpleGrid>
              {fromDate && toDate && fromDate < toDate && (
                <Box bg="blue.50" p={3} borderRadius="md">
                  <HStack>
                    <Icon as={FiCheck} color="green.500" />
                    <Text fontSize="sm" color="blue.700">
                      {availableRoomsCount} rooms available
                    </Text>
                  </HStack>
                </Box>
              )}
            </CardBody>
          </Card>

          {/* Guest Information */}
          <Card bg={cardBg} shadow="sm">
            <CardBody p={6}>
              <Heading size="sm" mb={4} color="gray.700">
                Guest Information
              </Heading>
              <VStack spacing={4} align="stretch">
                {/* Search Devotee */}
                <Box position="relative">
                  <InputGroup>
                    <InputLeftElement pointerEvents="none">
                      <Icon as={FiUser} color="gray.400" />
                    </InputLeftElement>
                    <Input
                      placeholder="Search Devotee"
                      value={devoteeSearchTerm}
                      onChange={(e) => setDevoteeSearchTerm(e.target.value)}
                      bg="white"
                    />
                  </InputGroup>
                  {devotees.length > 0 && (
                    <Box
                      position="absolute"
                      zIndex={10}
                      w="full"
                      mt={1}
                      bg="white"
                      borderWidth="1px"
                      borderRadius="md"
                      shadow="lg"
                      maxH="200px"
                      overflowY="auto"
                    >
                      {devotees.map((d) => (
                        <Box
                          key={d.name}
                          p={2}
                          cursor="pointer"
                          _hover={{ bg: 'gray.50' }}
                          onClick={() => handleDevoteeSelect(d.name, d.full_name)}
                        >
                          <Text fontSize="sm">{d.full_name}</Text>
                        </Box>
                      ))}
                    </Box>
                  )}
                  {devotee && (
                    <Text fontSize="xs" color="gray.600" mt={1}>
                      Selected: {devotees.find((d) => d.name === devotee)?.full_name || devotee}
                    </Text>
                  )}
                </Box>

                {/* Full Name */}
                <InputGroup>
                  <InputLeftElement pointerEvents="none">
                    <Icon as={FiUser} color="gray.400" />
                  </InputLeftElement>
                  <Input
                    placeholder="Full Name *"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    bg="white"
                  />
                </InputGroup>

                {/* Address */}
                <InputGroup>
                  <InputLeftElement pointerEvents="none" pt={2} alignItems="flex-start">
                    <Icon as={FiMapPin} color="gray.400" mt={2} />
                  </InputLeftElement>
                  <Textarea
                    placeholder="Address *"
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                    bg="white"
                    rows={3}
                    pl={10}
                  />
                </InputGroup>

                {/* Total Persons and Guest Type */}
                <SimpleGrid columns={2} spacing={4}>
                  <Box>
                    <Text fontSize="xs" color="gray.600" mb={1}>
                      Total Persons *
                    </Text>
                    <InputGroup>
                      <InputLeftElement pointerEvents="none">
                        <Icon as={FiUsers} color="gray.400" />
                      </InputLeftElement>
                      <NumberInput
                        value={totalPerson}
                        onChange={(_, val) => setTotalPerson(val)}
                        min={1}
                      >
                        <NumberInputField bg="white" pl={10} />
                      </NumberInput>
                    </InputGroup>
                  </Box>
                  <Box>
                    <Text fontSize="xs" color="gray.600" mb={1}>
                      Guest Type *
                    </Text>
                    <Select
                      value={guestType}
                      onChange={(e) => setGuestType(e.target.value)}
                      bg="white"
                      placeholder="Select Guest Type"
                    >
                      {roomTypes
                        .filter((rt, index, self) => index === self.findIndex((r) => r.guest_type === rt.guest_type))
                        .map((rt) => (
                          <option key={rt.guest_type} value={rt.guest_type}>
                            {rt.guest_type}
                          </option>
                        ))}
                    </Select>
                  </Box>
                </SimpleGrid>
              </VStack>
            </CardBody>
          </Card>

          {/* Select Rooms */}
          <Card bg={cardBg} shadow="sm">
            <CardBody p={6}>
              <Heading size="sm" mb={4} color="gray.700">
                Select Rooms
              </Heading>
              <Button
                leftIcon={<FiHome />}
                colorScheme="blue"
                w="full"
                onClick={() => setIsRoomModalOpen(true)}
                mb={4}
              >
                Select Rooms
              </Button>
              {fromDate && toDate && (
                <Text fontSize="sm" color="gray.600" mb={4}>
                  {availableRoomsCount} rooms available
                </Text>
              )}

              {selectedRooms.length > 0 && (
                <VStack spacing={4} align="stretch">
                  <SimpleGrid columns={{ base: 1, sm: 2, md: 3 }} spacing={3}>
                    {selectedRooms.map((room, index) => (
                      <Box
                        key={room.room_id}
                        p={3}
                        bg="gray.50"
                        borderRadius="md"
                        borderWidth="1px"
                        position="relative"
                      >
                        <IconButton
                          aria-label="Remove room"
                          icon={<FiX />}
                          size="xs"
                          variant="ghost"
                          position="absolute"
                          top={1}
                          right={1}
                          colorScheme="red"
                          onClick={() => {
                            setSelectedRooms(selectedRooms.filter((_, i) => i !== index));
                          }}
                        />
                        <VStack align="start" spacing={1}>
                          <Text fontWeight="semibold" fontSize="md">
                            {room.room_details}
                          </Text>
                          <Text fontSize="sm" color="gray.600">
                            {room.room_type || 'Room'}
                          </Text>
                          <Text fontSize="sm" fontWeight="medium" color="blue.600">
                            ₹{room.amount?.toLocaleString() || 0}
                          </Text>
                        </VStack>
                      </Box>
                    ))}
                  </SimpleGrid>
                  <Divider />
                  <HStack justify="space-between">
                    <Text fontWeight="semibold">Total Amount:</Text>
                    <Text fontSize="lg" fontWeight="bold" color="blue.600">
                      ₹{calculateTotalAmount().toLocaleString()}
                    </Text>
                  </HStack>
                </VStack>
              )}
            </CardBody>
          </Card>

          {/* Attachments */}
          <Card bg={cardBg} shadow="sm">
            <CardBody p={6}>
              <HStack mb={4}>
                <Icon as={FiCamera} color="blue.500" />
                <Heading size="sm" color="gray.700">
                  Attachments
                </Heading>
              </HStack>
              <Text fontSize="sm" color="gray.600" mb={4}>
                Images ({imagePreviews.length})
              </Text>
              <Box
                borderWidth="2px"
                borderStyle="dashed"
                borderColor="gray.300"
                borderRadius="md"
                p={8}
                textAlign="center"
                cursor="pointer"
                _hover={{ borderColor: 'blue.400', bg: 'blue.50' }}
                onClick={() => document.getElementById('image-upload')?.click()}
              >
                <Icon as={FiCamera} boxSize={8} color="gray.400" mb={2} />
                <Text fontSize="sm" fontWeight="medium" color="gray.600" mb={1}>
                  Add Images
                </Text>
                <Text fontSize="xs" color="gray.500">
                  Upload up to 5 images
                </Text>
              </Box>
              <Input
                id="image-upload"
                type="file"
                accept="image/*"
                multiple
                onChange={handleImageSelect}
                display="none"
              />

              {imagePreviews.length > 0 && (
                <SimpleGrid columns={3} spacing={4} mt={4}>
                  {imagePreviews.map((preview, index) => (
                    <Box key={index} position="relative">
                      <Image
                        src={preview}
                        alt={`Preview ${index + 1}`}
                        borderRadius="md"
                        objectFit="cover"
                        h="100px"
                        w="100%"
                      />
                      <IconButton
                        aria-label="Remove image"
                        icon={<FiX />}
                        size="xs"
                        colorScheme="red"
                        position="absolute"
                        top={1}
                        right={1}
                        onClick={() => handleRemoveImage(index)}
                      />
                    </Box>
                  ))}
                </SimpleGrid>
              )}
            </CardBody>
          </Card>

          {/* Submit Button */}
          <Button
            colorScheme="blue"
            size="lg"
            w="full"
            onClick={handleSubmit}
            isLoading={loading}
            loadingText="Creating Booking..."
          >
            Create Booking
          </Button>
        </VStack>
      </Container>

      {/* Room Selection Modal */}
      {isRoomModalOpen && (
        <RoomSelectionModal
          isOpen={isRoomModalOpen}
          onClose={() => setIsRoomModalOpen(false)}
          onSelect={handleRoomSelect}
          fromDate={fromDate}
          toDate={toDate}
          selectedRooms={selectedRooms}
          guestType={guestType}
          roomTypes={roomTypes}
        />
      )}
    </Box>
  );
};

export default NewBookingPage;


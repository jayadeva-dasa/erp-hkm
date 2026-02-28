// Room Selection Modal Component
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
  Input,
  InputGroup,
  InputLeftElement,
  Button,
  SimpleGrid,
  Card,
  CardBody,
  Checkbox,
  Badge,
  Box,
  Flex,
  Icon,
  useColorModeValue,
  Divider,
  IconButton,
  useDisclosure,
  NumberInput,
  NumberInputField,
} from '@chakra-ui/react';
import {
  FiSearch,
  FiHome,
  FiChevronUp,
  FiChevronDown,
  FiEdit2,
  FiDollarSign,
} from 'react-icons/fi';
import { guestHouseApi } from '../api/guestHouseApi';
import type { Room } from '../types';

interface SelectedRoom extends Room {
  amount: number;
  room_type?: string;
}

interface RoomSelectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (rooms: SelectedRoom[]) => void;
  fromDate: string;
  toDate: string;
  selectedRooms: SelectedRoom[];
  guestType: string;
  roomTypes: Array<{ room_type: string; guest_type: string; amount: number }>;
}

const RoomSelectionModal: React.FC<RoomSelectionModalProps> = ({
  isOpen,
  onClose,
  onSelect,
  fromDate,
  toDate,
  selectedRooms: initialSelectedRooms,
  guestType,
  roomTypes,
}) => {
  const [availableRooms, setAvailableRooms] = useState<Room[]>([]);
  const [filteredRooms, setFilteredRooms] = useState<Room[]>([]);
  const [selectedRooms, setSelectedRooms] = useState<SelectedRoom[]>(initialSelectedRooms);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedRoomType, setSelectedRoomType] = useState<string>('');
  const [expandedFloors, setExpandedFloors] = useState<Set<string>>(new Set());
  const [editingRoom, setEditingRoom] = useState<string | null>(null);
  const [editingAmount, setEditingAmount] = useState<number>(0);
  const [editingRoomType, setEditingRoomType] = useState<string | null>(null);
  const [editingBulkAmount, setEditingBulkAmount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(false);

  const cardBg = useColorModeValue('white', 'gray.700');
  const selectedBg = useColorModeValue('blue.50', 'blue.900');

  // Fetch available rooms
  useEffect(() => {
    const fetchRooms = async () => {
      if (!fromDate || !toDate || fromDate >= toDate) {
        return;
      }

      setLoading(true);
      try {
        const result = await guestHouseApi.getAvailableRooms(fromDate, toDate);
        const rooms = result.rooms || [];
        setAvailableRooms(rooms);
        setFilteredRooms(rooms);
      } catch (error: any) {
        console.error('Error fetching available rooms:', error);
      } finally {
        setLoading(false);
      }
    };

    if (isOpen) {
      fetchRooms();
      // Expand all floors by default
      const floors = new Set(availableRooms.map((r) => r.floor));
      setExpandedFloors(floors);
    }
  }, [isOpen, fromDate, toDate]);

  // Filter rooms
  useEffect(() => {
    let filtered = availableRooms;

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter((room) =>
        room.room_details.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Filter by room type
    if (selectedRoomType) {
      filtered = filtered.filter((room) => room.room_type === selectedRoomType);
    }

    setFilteredRooms(filtered);
  }, [searchTerm, selectedRoomType, availableRooms]);

  // Get unique room types
  const uniqueRoomTypes = Array.from(
    new Set(roomTypes.map((rt) => rt.room_type))
  );

  // Get rooms by floor
  const roomsByFloor = filteredRooms.reduce((acc, room) => {
    if (!acc[room.floor]) {
      acc[room.floor] = [];
    }
    acc[room.floor].push(room);
    return acc;
  }, {} as Record<string, Room[]>);

  const toggleFloor = (floor: string) => {
    const newExpanded = new Set(expandedFloors);
    if (newExpanded.has(floor)) {
      newExpanded.delete(floor);
    } else {
      newExpanded.add(floor);
    }
    setExpandedFloors(newExpanded);
  };

  const toggleRoomSelection = (room: Room) => {
    const isSelected = selectedRooms.some((sr) => sr.room_id === room.room_id);

    if (isSelected) {
      setSelectedRooms(selectedRooms.filter((sr) => sr.room_id !== room.room_id));
    } else {
      // Get default amount from room types
      const defaultAmount =
        roomTypes.find((rt) => rt.guest_type === guestType)?.amount || 0;

      const newRoom: SelectedRoom = {
        ...room,
        amount: defaultAmount,
        room_type: room.room_type || roomTypes.find((rt) => rt.guest_type === guestType)?.room_type,
      };
      setSelectedRooms([...selectedRooms, newRoom]);
    }
  };

  const handleEditAmount = (roomId: string, currentAmount: number) => {
    setEditingRoom(roomId);
    setEditingAmount(currentAmount);
  };

  const saveAmount = (roomId: string) => {
    setSelectedRooms(
      selectedRooms.map((room) =>
        room.room_id === roomId ? { ...room, amount: editingAmount } : room
      )
    );
    setEditingRoom(null);
  };

  const handleBulkEditClick = (roomType: string) => {
    // Get the current amount for rooms of this type (use first room's amount as default)
    const roomsOfType = selectedRooms.filter((r) => r.room_type === roomType);
    const defaultAmount = roomsOfType.length > 0 ? roomsOfType[0].amount : 0;
    setEditingRoomType(roomType);
    setEditingBulkAmount(defaultAmount);
  };

  const saveBulkAmount = () => {
    if (editingRoomType) {
      setSelectedRooms(
        selectedRooms.map((room) =>
          room.room_type === editingRoomType
            ? { ...room, amount: editingBulkAmount }
            : room
        )
      );
      setEditingRoomType(null);
    }
  };

  const getRoomAmount = (roomId: string) => {
    const selected = selectedRooms.find((sr) => sr.room_id === roomId);
    return selected?.amount || 0;
  };

  const isRoomSelected = (roomId: string) => {
    return selectedRooms.some((sr) => sr.room_id === roomId);
  };

  const calculateTotal = () => {
    return selectedRooms.reduce((sum, room) => sum + (room.amount || 0), 0);
  };

  const handleConfirm = () => {
    onSelect(selectedRooms);
    onClose();
  };

  // Group selected rooms by room type for bulk edit
  const selectedByType = selectedRooms.reduce((acc, room) => {
    const type = room.room_type || 'Other';
    if (!acc[type]) {
      acc[type] = [];
    }
    acc[type].push(room);
    return acc;
  }, {} as Record<string, SelectedRoom[]>);

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="xl" isCentered>
      <ModalOverlay />
      <ModalContent maxH="90vh" display="flex" flexDirection="column">
        <ModalHeader>
          <HStack justify="space-between">
            <Text>Available Rooms</Text>
            <Badge colorScheme="blue" fontSize="sm">
              {filteredRooms.length}/{availableRooms.length}
            </Badge>
          </HStack>
        </ModalHeader>
        <ModalCloseButton />
        <ModalBody flex="1" overflowY="auto" pb={4}>
          <VStack spacing={4} align="stretch">
            {/* Search */}
            <InputGroup>
              <InputLeftElement pointerEvents="none">
                <Icon as={FiSearch} color="gray.400" />
              </InputLeftElement>
              <Input
                placeholder="Search by room number..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                bg="white"
              />
            </InputGroup>

            {/* Room Type Filters */}
            {uniqueRoomTypes.length > 0 && (
              <HStack spacing={2} flexWrap="wrap">
                <Text fontSize="sm" fontWeight="medium">
                  Type:
                </Text>
                <Button
                  size="sm"
                  variant={!selectedRoomType ? 'solid' : 'outline'}
                  colorScheme="blue"
                  onClick={() => setSelectedRoomType('')}
                >
                  All
                </Button>
                {uniqueRoomTypes.map((type) => (
                  <Button
                    key={type}
                    size="sm"
                    variant={selectedRoomType === type ? 'solid' : 'outline'}
                    colorScheme="blue"
                    onClick={() => setSelectedRoomType(type)}
                  >
                    {type}
                  </Button>
                ))}
              </HStack>
            )}

            {/* Rooms by Floor */}
            {Object.entries(roomsByFloor)
              .sort(([a], [b]) => a.localeCompare(b))
              .map(([floor, rooms]) => (
                <Box key={floor}>
                  <Box
                    as="button"
                    w="full"
                    p={3}
                    bg="blue.50"
                    borderRadius="md"
                    onClick={() => toggleFloor(floor)}
                    mb={2}
                  >
                    <HStack justify="space-between">
                      <HStack>
                        <Text fontWeight="semibold">Floor {floor}</Text>
                        <Badge colorScheme="blue">{rooms.length}</Badge>
                      </HStack>
                      <Icon
                        as={expandedFloors.has(floor) ? FiChevronUp : FiChevronDown}
                      />
                    </HStack>
                  </Box>

                  {expandedFloors.has(floor) && (
                    <SimpleGrid columns={3} spacing={3} mt={2}>
                      {rooms.map((room) => {
                        const isSelected = isRoomSelected(room.room_id);
                        const amount = getRoomAmount(room.room_id);

                        return (
                          <Card
                            key={room.room_id}
                            bg={isSelected ? selectedBg : cardBg}
                            borderWidth={isSelected ? '2px' : '1px'}
                            borderColor={isSelected ? 'blue.500' : 'gray.200'}
                            cursor="pointer"
                            onClick={() => toggleRoomSelection(room)}
                            position="relative"
                          >
                            <CardBody p={3}>
                              <VStack spacing={1} align="stretch">
                                <HStack justify="space-between">
                                  <VStack align="start" spacing={0}>
                                    <Text fontWeight="semibold" fontSize="sm">
                                      {room.room_details}
                                    </Text>
                                    {room.room_type && (
                                      <Text fontSize="xs" color="gray.600">
                                        {room.room_type}
                                      </Text>
                                    )}
                                  </VStack>
                                  <Checkbox
                                    isChecked={isSelected}
                                    colorScheme="blue"
                                    onChange={() => toggleRoomSelection(room)}
                                    onClick={(e) => e.stopPropagation()}
                                  />
                                </HStack>
                                {isSelected && (
                                  <HStack justify="space-between" mt={2}>
                                    <Text fontSize="xs" color="gray.600">
                                      ₹{amount.toLocaleString()}
                                    </Text>
                                    <IconButton
                                      aria-label="Edit amount"
                                      icon={<FiEdit2 />}
                                      size="xs"
                                      variant="ghost"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        handleEditAmount(room.room_id, amount);
                                      }}
                                    />
                                  </HStack>
                                )}
                              </VStack>
                            </CardBody>
                          </Card>
                        );
                      })}
                    </SimpleGrid>
                  )}
                </Box>
              ))}

            {loading && (
              <Box textAlign="center" py={8}>
                <Text color="gray.600">Loading rooms...</Text>
              </Box>
            )}

            {!loading && filteredRooms.length === 0 && (
              <Box textAlign="center" py={8}>
                <Text color="gray.600">No rooms available</Text>
              </Box>
            )}
          </VStack>
        </ModalBody>

        {/* Selected Rooms Summary */}
        {selectedRooms.length > 0 && (
          <Box borderTopWidth="1px" p={4} bg="gray.50">
            <VStack spacing={3} align="stretch">
              <HStack justify="space-between">
                <Text fontWeight="semibold">
                  {selectedRooms.length} room{selectedRooms.length > 1 ? 's' : ''} selected
                </Text>
                <Text fontWeight="semibold">
                  Total: ₹{calculateTotal().toLocaleString()}
                </Text>
              </HStack>

              {/* Bulk Edit by Room Type */}
              {Object.keys(selectedByType).length > 0 && (
                <Box>
                  <Text fontSize="sm" fontWeight="medium" mb={2}>
                    Bulk Edit by Room Type
                  </Text>
                  <HStack spacing={2} flexWrap="wrap">
                    {Object.entries(selectedByType).map(([type, rooms]) => (
                      <Box key={type}>
                        {editingRoomType === type ? (
                          <HStack spacing={2}>
                            <NumberInput
                              value={editingBulkAmount}
                              onChange={(_, val) => setEditingBulkAmount(val)}
                              size="sm"
                              w="120px"
                            >
                              <NumberInputField />
                            </NumberInput>
                            <Button
                              size="xs"
                              colorScheme="blue"
                              onClick={saveBulkAmount}
                            >
                              Save
                            </Button>
                            <Button
                              size="xs"
                              variant="ghost"
                              onClick={() => setEditingRoomType(null)}
                            >
                              Cancel
                            </Button>
                          </HStack>
                        ) : (
                          <Badge
                            colorScheme="blue"
                            fontSize="sm"
                            px={3}
                            py={1}
                            borderRadius="full"
                            cursor="pointer"
                            _hover={{ bg: 'blue.600', color: 'white' }}
                            onClick={() => handleBulkEditClick(type)}
                          >
                            {type} ({rooms.length}){' '}
                            <Icon as={FiEdit2} ml={1} boxSize={3} />
                          </Badge>
                        )}
                      </Box>
                    ))}
                  </HStack>
                </Box>
              )}

              {/* Selected Rooms List */}
              <VStack spacing={2} align="stretch" maxH="150px" overflowY="auto">
                {selectedRooms.map((room) => (
                  <Box
                    key={room.room_id}
                    p={2}
                    bg="white"
                    borderRadius="md"
                    borderWidth="1px"
                  >
                    <HStack justify="space-between">
                      <VStack align="start" spacing={0}>
                        <Text fontSize="sm" fontWeight="medium">
                          {room.room_details}
                        </Text>
                        <Text fontSize="xs" color="gray.600">
                          {room.room_type || 'Room'}
                        </Text>
                      </VStack>
                      <HStack>
                        {editingRoom === room.room_id ? (
                          <HStack>
                            <NumberInput
                              value={editingAmount}
                              onChange={(_, val) => setEditingAmount(val)}
                              size="sm"
                              w="100px"
                            >
                              <NumberInputField />
                            </NumberInput>
                            <Button
                              size="xs"
                              colorScheme="blue"
                              onClick={() => saveAmount(room.room_id)}
                            >
                              Save
                            </Button>
                            <Button
                              size="xs"
                              variant="ghost"
                              onClick={() => setEditingRoom(null)}
                            >
                              Cancel
                            </Button>
                          </HStack>
                        ) : (
                          <>
                            <Text fontSize="sm" fontWeight="medium">
                              ₹{room.amount?.toLocaleString() || 0}
                            </Text>
                            <IconButton
                              aria-label="Edit amount"
                              icon={<FiEdit2 />}
                              size="xs"
                              variant="ghost"
                              onClick={() => handleEditAmount(room.room_id, room.amount || 0)}
                            />
                          </>
                        )}
                      </HStack>
                    </HStack>
                  </Box>
                ))}
              </VStack>

              <Button
                colorScheme="blue"
                w="full"
                onClick={handleConfirm}
                size="md"
              >
                Confirm Selection ({selectedRooms.length})
              </Button>
            </VStack>
          </Box>
        )}

        {selectedRooms.length === 0 && (
          <Box borderTopWidth="1px" p={4} textAlign="center">
            <Text color="gray.600">No Rooms Selected</Text>
          </Box>
        )}
      </ModalContent>
    </Modal>
  );
};

export default RoomSelectionModal;


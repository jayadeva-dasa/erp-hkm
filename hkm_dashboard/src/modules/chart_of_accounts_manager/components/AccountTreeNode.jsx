import React, { useState } from 'react';
import { Draggable, Droppable } from 'react-beautiful-dnd';
import {
  Box,
  HStack,
  Text,
  Icon,
  IconButton,
  Tooltip,
  useColorModeValue,
  Collapse,
} from '@chakra-ui/react';
import { FiChevronRight, FiChevronDown, FiFolder, FiFile, FiInfo, FiArrowRight } from 'react-icons/fi';
import { formatCurrency, getAccountTypeColor } from '../utils/accountUtils';

const AccountTreeNode = ({
  account,
  index,
  onToggle,
  onAccountClick,
  onMoveClick,
  showBalance,
  currency,
  searchTerm,
  compact,
}) => {
  const [isHovered, setIsHovered] = useState(false);

  const bgColor = useColorModeValue('white', 'gray.800');
  const hoverBg = useColorModeValue('gray.50', 'gray.700');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const textColor = useColorModeValue('gray.800', 'gray.200');
  const mutedColor = useColorModeValue('gray.500', 'gray.400');

  const hasChildren = account.children && account.children.length > 0;
  const isExpanded = account.expanded;
  const accountTypeColor = getAccountTypeColor(account.root_type);

  const highlightText = (text, term) => {
    if (!term) return text;
    const regex = new RegExp(`(${term})`, 'gi');
    const parts = text.split(regex);
    return parts.map((part, i) =>
      regex.test(part) ? (
        <Text as="span" key={i} bg="yellow.200" fontWeight="bold">
          {part}
        </Text>
      ) : (
        part
      )
    );
  };

  const py = compact ? 1 : 2;
  const px = compact ? 2 : 3;
  const indent = compact ? 20 : 32;
  const fontSize = compact ? 'xs' : 'sm';

  return (
    <Draggable draggableId={account.name} index={index}>
      {(provided, snapshot) => (
        <Box
          ref={provided.innerRef}
          {...provided.draggableProps}
          {...provided.dragHandleProps}
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
        >
          <Droppable droppableId={account.name} type="ACCOUNT" isDropDisabled={!account.is_group}>
            {(providedDrop, snapshotDrop) => (
              <Box ref={providedDrop.innerRef} {...providedDrop.droppableProps}>
                <HStack
                  spacing={1.5}
                  py={py}
                  px={px}
                  bg={snapshotDrop.isDraggingOver ? 'blue.50' : isHovered ? hoverBg : bgColor}
                  borderWidth="1px"
                  borderColor={snapshotDrop.isDraggingOver ? 'blue.300' : borderColor}
                  borderRadius="sm"
                  borderLeftWidth="3px"
                  borderLeftColor={`${accountTypeColor}.400`}
                  mb={0.5}
                  cursor="pointer"
                  transition="all 0.15s"
                  opacity={snapshot.isDragging ? 0.5 : 1}
                  ml={`${account.level * indent}px`}
                  _hover={{ borderLeftColor: `${accountTypeColor}.600` }}
                >
                  <Box w="16px" flexShrink={0}>
                    {hasChildren ? (
                      <IconButton
                        icon={isExpanded ? <FiChevronDown /> : <FiChevronRight />}
                        size="xs"
                        variant="ghost"
                        minW="16px"
                        w="16px"
                        h="16px"
                        onClick={(e) => {
                          e.stopPropagation();
                          onToggle(account.name);
                        }}
                        aria-label={isExpanded ? 'Collapse' : 'Expand'}
                      />
                    ) : null}
                  </Box>
                  <Icon
                    as={account.is_group ? FiFolder : FiFile}
                    color={`${accountTypeColor}.500`}
                    boxSize={3}
                    flexShrink={0}
                  />
                  <Box flex="1" minW={0} onClick={() => onAccountClick(account)}>
                    <Text fontSize={fontSize} fontWeight={account.is_group ? 'semibold' : 'normal'} color={textColor} noOfLines={1}>
                      {highlightText(account.account_name, searchTerm)}
                    </Text>
                    {account.account_number && !compact && (
                      <Text fontSize="xs" color={mutedColor}>#{account.account_number}</Text>
                    )}
                  </Box>
                  {showBalance && account.balance !== undefined && (
                    <Text fontSize={fontSize} fontWeight="medium" color={account.balance >= 0 ? 'blue.600' : 'orange.600'} minW="100px" textAlign="right" fontFamily="mono" flexShrink={0}>
                      {formatCurrency(account.balance, currency, true)}
                    </Text>
                  )}
                  <HStack spacing={0} flexShrink={0}>
                    <Tooltip label="Change parent">
                      <IconButton
                        icon={<FiArrowRight />}
                        size="xs"
                        variant="ghost"
                        minW="20px"
                        w="20px"
                        h="20px"
                        onClick={(e) => {
                          e.stopPropagation();
                          onMoveClick(account);
                        }}
                        aria-label="Change parent"
                      />
                    </Tooltip>
                    <Tooltip label="Details">
                      <IconButton
                        icon={<FiInfo />}
                        size="xs"
                        variant="ghost"
                        minW="20px"
                        w="20px"
                        h="20px"
                        onClick={(e) => {
                          e.stopPropagation();
                          onAccountClick(account);
                        }}
                        aria-label="Details"
                      />
                    </Tooltip>
                  </HStack>
                </HStack>
                {providedDrop.placeholder}
                {hasChildren && (
                  <Collapse in={isExpanded} animateOpacity>
                    <Box>
                      {account.children.map((child, idx) => (
                        <AccountTreeNode
                          key={child.name}
                          account={child}
                          index={idx}
                          onToggle={onToggle}
                          onAccountClick={onAccountClick}
                          onMoveClick={onMoveClick}
                          showBalance={showBalance}
                          currency={currency}
                          searchTerm={searchTerm}
                          compact={compact}
                        />
                      ))}
                    </Box>
                  </Collapse>
                )}
              </Box>
            )}
          </Droppable>
        </Box>
      )}
    </Draggable>
  );
};

export default AccountTreeNode;

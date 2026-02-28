import React from 'react';
import {
  HStack,
  FormControl,
  FormLabel,
  Select,
  Input,
  Button,
  Switch,
  Text,
  InputGroup,
  InputLeftElement,
  Icon,
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  Tooltip,
} from '@chakra-ui/react';
import { FiSearch, FiRefreshCw, FiDownload } from 'react-icons/fi';

const ChartFilters = ({
  companies,
  selectedCompany,
  onCompanyChange,
  asOnDate,
  onAsOnDateChange,
  maxDepth,
  onMaxDepthChange,
  showBalance,
  onShowBalanceChange,
  showDisabled,
  onShowDisabledChange,
  searchTerm,
  onSearchChange,
  onRefresh,
  onExport,
  loading,
}) => (
  <HStack spacing={3} align="flex-end" flexWrap="wrap">
    <FormControl w="200px">
      <FormLabel fontSize="xs" mb={0}>Company</FormLabel>
      <Select
        value={selectedCompany}
        onChange={(e) => onCompanyChange(e.target.value)}
        size="sm"
        disabled={loading}
      >
        <option value="">Select</option>
        {companies.map((company) => (
          <option key={company.name} value={company.name}>
            {company.name}
          </option>
        ))}
      </Select>
    </FormControl>
    <FormControl w="130px">
      <FormLabel fontSize="xs" mb={0}>As on</FormLabel>
      <Input
        type="date"
        value={asOnDate}
        onChange={(e) => onAsOnDateChange(e.target.value)}
        size="sm"
        disabled={loading}
      />
    </FormControl>
    <FormControl w="160px">
      <FormLabel fontSize="xs" mb={0}>Search</FormLabel>
      <InputGroup size="sm">
        <InputLeftElement pointerEvents="none">
          <Icon as={FiSearch} color="gray.400" boxSize={3} />
        </InputLeftElement>
        <Input
          placeholder="Name or #"
          value={searchTerm}
          onChange={(e) => onSearchChange(e.target.value)}
        />
      </InputGroup>
    </FormControl>
    <FormControl w="80px">
      <FormLabel fontSize="xs" mb={0}>Depth</FormLabel>
      <Slider
        value={maxDepth === null ? 10 : maxDepth}
        min={1}
        max={10}
        step={1}
        size="sm"
        onChange={(val) => onMaxDepthChange(val === 10 ? null : val)}
      >
        <SliderTrack>
          <SliderFilledTrack bg="blue.500" />
        </SliderTrack>
        <SliderThumb boxSize={3} />
      </Slider>
    </FormControl>
    <Text fontSize="xs" color="gray.500">{maxDepth === null ? 'All' : maxDepth}</Text>
    <HStack spacing={2}>
      <HStack spacing={1}>
        <Switch
          isChecked={showBalance}
          onChange={(e) => onShowBalanceChange(e.target.checked)}
          size="sm"
          colorScheme="blue"
        />
        <Text fontSize="xs">Bal</Text>
      </HStack>
      <HStack spacing={1}>
        <Switch
          isChecked={showDisabled}
          onChange={(e) => onShowDisabledChange(e.target.checked)}
          size="sm"
          colorScheme="orange"
        />
        <Text fontSize="xs">Disabled</Text>
      </HStack>
    </HStack>
    <Button leftIcon={<FiRefreshCw />} colorScheme="blue" size="sm" onClick={onRefresh} isLoading={loading} loadingText="…">
      Load
    </Button>
    <Tooltip label="Export CSV">
      <Button leftIcon={<FiDownload />} size="sm" variant="outline" onClick={onExport}>
        Export
      </Button>
    </Tooltip>
  </HStack>
);

export default ChartFilters;

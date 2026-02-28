import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Heading,
  Button,
  FormControl,
  FormLabel,
  Input,
  Select,
  Checkbox,
  VStack,
  HStack,
  useToast,
  Divider,
  Text,
  SimpleGrid,
  NumberInput,
  NumberInputField,
  Textarea,
  Collapse,
} from '@chakra-ui/react';
import { FiSave, FiArrowLeft } from 'react-icons/fi';
import PageHeader from '../../../components/shared/PageHeader';
import apiClient from '../../../services/apiClient';
import { SearchableSelect, SelectOption } from '../../asset_reco/components/SearchableSelect';

interface FormData {
  item_code: string;
  asset_name: string;
  asset_category: string;
  company: string;
  custodian_department: string;
  location: string;
  sub_custodian: string;
  is_existing_asset: boolean;
  purchase_date: string;
  available_for_use_date: string;
  purchase_receipt: string;
  purchase_invoice: string;
  gross_purchase_amount: number;
  asset_quantity: number;
  calculate_depreciation: boolean;
  depreciation_method: string;
  frequency_of_depreciation: number;
  total_number_of_depreciations: number;
  depreciation_start_date: string;
  expected_value_after_useful_life: number;
  opening_accumulated_depreciation: number;
  opening_number_of_booked_depreciations: number;
  fixed_asset_account: string;
  accumulated_depreciation_account: string;
  depreciation_expense_account: string;
  cwip_account: string;
  cost_center: string;
  policy_number: string;
  insurer: string;
  insured_value: number;
  insurance_start_date: string;
  insurance_end_date: string;
  maintenance_required: boolean;
  remarks: string;
  asset_specifications: any[];
}

const CreateAssetPage: React.FC = () => {
  const navigate = useNavigate();
  const toast = useToast();
  const [loading, setLoading] = useState(false);
  const [itemOptions, setItemOptions] = useState<SelectOption[]>([]);
  const [isSearchingItems, setIsSearchingItems] = useState(false);
  const [companyOptions, setCompanyOptions] = useState<SelectOption[]>([]);
  const [isSearchingCompanies, setIsSearchingCompanies] = useState(false);
  const [departmentOptions, setDepartmentOptions] = useState<SelectOption[]>([]);
  const [isSearchingDepartments, setIsSearchingDepartments] = useState(false);
  const [purchaseReceiptOptions, setPurchaseReceiptOptions] = useState<SelectOption[]>([]);
  const [isSearchingPurchaseReceipts, setIsSearchingPurchaseReceipts] = useState(false);
  const [purchaseInvoiceOptions, setPurchaseInvoiceOptions] = useState<SelectOption[]>([]);
  const [isSearchingPurchaseInvoices, setIsSearchingPurchaseInvoices] = useState(false);
  const [assetCategories, setAssetCategories] = useState<any[]>([]);
  const [accounts, setAccounts] = useState<any[]>([]);
  const [costCenters, setCostCenters] = useState<any[]>([]);
  const [assetSpecifications, setAssetSpecifications] = useState<any[]>([]);
  const itemSearchTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const companySearchTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const departmentSearchTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const purchaseReceiptSearchTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const purchaseInvoiceSearchTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  
  const [formData, setFormData] = useState<FormData>({
    item_code: '',
    asset_name: '',
    asset_category: '',
    company: '',
    custodian_department: '',
    location: '',
    sub_custodian: '',
    is_existing_asset: false,
    purchase_date: new Date().toISOString().split('T')[0],
    available_for_use_date: new Date().toISOString().split('T')[0],
    purchase_receipt: '',
    purchase_invoice: '',
    gross_purchase_amount: 0,
    asset_quantity: 1,
    calculate_depreciation: false,
    depreciation_method: 'Straight Line',
    frequency_of_depreciation: 12,
    total_number_of_depreciations: 60,
    depreciation_start_date: '',
    expected_value_after_useful_life: 0,
    opening_accumulated_depreciation: 0,
    opening_number_of_booked_depreciations: 0,
    fixed_asset_account: '',
    accumulated_depreciation_account: '',
    depreciation_expense_account: '',
    cwip_account: '',
    cost_center: '',
    policy_number: '',
    insurer: '',
    insured_value: 0,
    insurance_start_date: '',
    insurance_end_date: '',
    maintenance_required: false,
    remarks: '',
    asset_specifications: [],
  });

  useEffect(() => {
    fetchMasterData();
    
    // Cleanup timeouts on unmount
    return () => {
      if (itemSearchTimeoutRef.current) {
        clearTimeout(itemSearchTimeoutRef.current);
      }
      if (companySearchTimeoutRef.current) {
        clearTimeout(companySearchTimeoutRef.current);
      }
      if (departmentSearchTimeoutRef.current) {
        clearTimeout(departmentSearchTimeoutRef.current);
      }
      if (purchaseReceiptSearchTimeoutRef.current) {
        clearTimeout(purchaseReceiptSearchTimeoutRef.current);
      }
      if (purchaseInvoiceSearchTimeoutRef.current) {
        clearTimeout(purchaseInvoiceSearchTimeoutRef.current);
      }
    };
  }, []);

  const searchItems = async (searchTerm: string = '', isInitialLoad: boolean = false) => {
    setIsSearchingItems(true);
    try {
      const filters: any[] = [['is_fixed_asset', '=', 1]];
      const orFilters: any[] = [];
      
      // Add search filter if search term is provided - search by both name (item code) and item_name
      if (searchTerm && searchTerm.trim()) {
        orFilters.push(['name', 'like', `%${searchTerm}%`]);
        orFilters.push(['item_name', 'like', `%${searchTerm}%`]);
      }
      
      const params: any = {
        fields: JSON.stringify(['name', 'item_name', 'asset_category']),
        filters: JSON.stringify(filters),
        limit_page_length: 50,
        order_by: 'item_name asc',
      };
      
      // Add or_filters if we have a search term
      if (orFilters.length > 0) {
        params.or_filters = JSON.stringify(orFilters);
      }
      
      const itemsRes = await apiClient.get('/api/resource/Item', { params });
      
      const items = itemsRes.data.data || [];
      const options: SelectOption[] = items.map((item: any) => ({
        value: item.name,
        label: `${item.name} - ${item.item_name}`,
      }));
      
      setItemOptions(options);
      
      // Auto-select first item if field is empty and this is initial load (no search term)
      if (isInitialLoad && !searchTerm && options.length > 0 && !formData.item_code) {
        const firstItem = options[0];
        // Update form data directly and fetch item details
        setFormData((prev) => {
          const updated = { ...prev, item_code: firstItem.value };
          // Fetch full item details to get asset_category
          apiClient.get(`/api/resource/Item/${firstItem.value}`, {
            params: {
              fields: JSON.stringify(['item_name', 'asset_category']),
            },
          }).then((response) => {
            const item = response.data.data;
            if (item) {
              setFormData((prev) => {
                const updated = { ...prev };
                if (item.item_name) updated.asset_name = item.item_name;
                if (item.asset_category) {
                  updated.asset_category = item.asset_category;
                  fetchAssetCategoryAccounts(item.asset_category, prev.company);
                  fetchAssetSpecifications(item.asset_category);
                }
                return updated;
              });
            }
          }).catch((error) => {
            console.error('Error fetching item details:', error);
          });
          return updated;
        });
      }
    } catch (error: any) {
      console.error('Error searching items:', error);
      toast({
        title: 'Error searching items',
        description: error.message,
        status: 'error',
        duration: 3000,
      });
      setItemOptions([]);
    } finally {
      setIsSearchingItems(false);
    }
  };

  const handleItemSearch = (searchTerm: string) => {
    // Clear previous timeout
    if (itemSearchTimeoutRef.current) {
      clearTimeout(itemSearchTimeoutRef.current);
    }
    
    // Debounce search - wait 300ms after user stops typing
    itemSearchTimeoutRef.current = setTimeout(() => {
      searchItems(searchTerm);
    }, 300);
  };

  const searchDepartments = async (searchTerm: string = '', isInitialLoad: boolean = false) => {
    setIsSearchingDepartments(true);
    try {
      const filters: any[] = [];
      
      // Add search filter if search term is provided
      if (searchTerm && searchTerm.trim()) {
        filters.push(['name', 'like', `%${searchTerm}%`]);
      }
      
      const deptRes = await apiClient.get('/api/resource/Execution Department', {
        params: {
          fields: JSON.stringify(['name']),
          filters: filters.length > 0 ? JSON.stringify(filters) : undefined,
          limit_page_length: 50,
          order_by: 'name asc',
        },
      });
      
      const departments = deptRes.data.data || [];
      const options: SelectOption[] = departments.map((dept: any) => ({
        value: dept.name,
        label: dept.name,
      }));
      
      setDepartmentOptions(options);
      
      // Auto-select first department if field is empty and this is initial load (no search term)
      if (isInitialLoad && !searchTerm && options.length > 0 && !formData.custodian_department) {
        const firstDept = options[0];
        setFormData((prev) => ({ ...prev, custodian_department: firstDept.value }));
      }
    } catch (error: any) {
      console.error('Error searching departments:', error);
      toast({
        title: 'Error searching departments',
        description: error.message,
        status: 'error',
        duration: 3000,
      });
      setDepartmentOptions([]);
    } finally {
      setIsSearchingDepartments(false);
    }
  };

  const handleDepartmentSearch = (searchTerm: string) => {
    if (departmentSearchTimeoutRef.current) {
      clearTimeout(departmentSearchTimeoutRef.current);
    }
    
    departmentSearchTimeoutRef.current = setTimeout(() => {
      searchDepartments(searchTerm);
    }, 300);
  };

  const searchPurchaseReceipts = async (searchTerm: string = '') => {
    setIsSearchingPurchaseReceipts(true);
    try {
      const filters: any[] = [['docstatus', '=', 1]];
      
      // Add search filter if search term is provided
      if (searchTerm && searchTerm.trim()) {
        filters.push(['name', 'like', `%${searchTerm}%`]);
      }
      
      const prRes = await apiClient.get('/api/resource/Purchase Receipt', {
        params: {
          fields: JSON.stringify(['name', 'posting_date']),
          filters: JSON.stringify(filters),
          limit_page_length: 50,
          order_by: 'posting_date desc',
        },
      });
      
      const receipts = prRes.data.data || [];
      const options: SelectOption[] = [
        { value: '', label: 'None' },
        ...receipts.map((pr: any) => ({
          value: pr.name,
          label: `${pr.name} - ${pr.posting_date || ''}`,
        })),
      ];
      
      setPurchaseReceiptOptions(options);
    } catch (error: any) {
      console.error('Error searching purchase receipts:', error);
      toast({
        title: 'Error searching purchase receipts',
        description: error.message,
        status: 'error',
        duration: 3000,
      });
      setPurchaseReceiptOptions([]);
    } finally {
      setIsSearchingPurchaseReceipts(false);
    }
  };

  const handlePurchaseReceiptSearch = (searchTerm: string) => {
    if (purchaseReceiptSearchTimeoutRef.current) {
      clearTimeout(purchaseReceiptSearchTimeoutRef.current);
    }
    
    purchaseReceiptSearchTimeoutRef.current = setTimeout(() => {
      searchPurchaseReceipts(searchTerm);
    }, 300);
  };

  const searchPurchaseInvoices = async (searchTerm: string = '') => {
    setIsSearchingPurchaseInvoices(true);
    try {
      const filters: any[] = [['docstatus', '=', 1]];
      
      // Add search filter if search term is provided
      if (searchTerm && searchTerm.trim()) {
        filters.push(['name', 'like', `%${searchTerm}%`]);
      }
      
      const piRes = await apiClient.get('/api/resource/Purchase Invoice', {
        params: {
          fields: JSON.stringify(['name', 'posting_date']),
          filters: JSON.stringify(filters),
          limit_page_length: 50,
          order_by: 'posting_date desc',
        },
      });
      
      const invoices = piRes.data.data || [];
      const options: SelectOption[] = [
        { value: '', label: 'None' },
        ...invoices.map((pi: any) => ({
          value: pi.name,
          label: `${pi.name} - ${pi.posting_date || ''}`,
        })),
      ];
      
      setPurchaseInvoiceOptions(options);
    } catch (error: any) {
      console.error('Error searching purchase invoices:', error);
      toast({
        title: 'Error searching purchase invoices',
        description: error.message,
        status: 'error',
        duration: 3000,
      });
      setPurchaseInvoiceOptions([]);
    } finally {
      setIsSearchingPurchaseInvoices(false);
    }
  };

  const handlePurchaseInvoiceSearch = (searchTerm: string) => {
    if (purchaseInvoiceSearchTimeoutRef.current) {
      clearTimeout(purchaseInvoiceSearchTimeoutRef.current);
    }
    
    purchaseInvoiceSearchTimeoutRef.current = setTimeout(() => {
      searchPurchaseInvoices(searchTerm);
    }, 300);
  };

  const searchCompanies = async (searchTerm: string = '', isInitialLoad: boolean = false) => {
    setIsSearchingCompanies(true);
    try {
      const filters: any[] = [];
      
      // Add search filter if search term is provided
      if (searchTerm && searchTerm.trim()) {
        filters.push(['company_name', 'like', `%${searchTerm}%`]);
      }
      
      const companiesRes = await apiClient.get('/api/resource/Company', {
        params: {
          fields: JSON.stringify(['name', 'company_name']),
          filters: filters.length > 0 ? JSON.stringify(filters) : undefined,
          limit_page_length: 50,
          order_by: 'company_name asc',
        },
      });
      
      const companies = companiesRes.data.data || [];
      const options: SelectOption[] = companies.map((company: any) => ({
        value: company.name,
        label: company.company_name || company.name,
      }));
      
      setCompanyOptions(options);
      
      // Auto-select first company if field is empty and this is initial load (no search term)
      if (isInitialLoad && !searchTerm && options.length > 0 && !formData.company) {
        const firstCompany = options[0];
        setFormData((prev) => {
          const updated = { ...prev, company: firstCompany.value };
          // Fetch accounts and cost centers for the selected company
          fetchAccountsAndCostCenters(firstCompany.value);
          return updated;
        });
      }
    } catch (error: any) {
      console.error('Error searching companies:', error);
      toast({
        title: 'Error searching companies',
        description: error.message,
        status: 'error',
        duration: 3000,
      });
      setCompanyOptions([]);
    } finally {
      setIsSearchingCompanies(false);
    }
  };

  const handleCompanySearch = (searchTerm: string) => {
    if (companySearchTimeoutRef.current) {
      clearTimeout(companySearchTimeoutRef.current);
    }
    
    companySearchTimeoutRef.current = setTimeout(() => {
      searchCompanies(searchTerm);
    }, 300);
  };

  const fetchAccountsAndCostCenters = async (company: string) => {
    if (!company) return;
    
    try {
      // Fetch Accounts
      const accRes = await apiClient.get('/api/resource/Account', {
        params: {
          fields: JSON.stringify(['name', 'account_name', 'account_type']),
          filters: JSON.stringify([
            ['company', '=', company],
            ['is_group', '=', 0],
          ]),
          limit_page_length: 500,
        },
      });
      setAccounts(accRes.data.data || []);

      // Fetch Cost Centers
      const ccRes = await apiClient.get('/api/resource/Cost Center', {
        params: {
          fields: JSON.stringify(['name', 'cost_center_name']),
          filters: JSON.stringify([
            ['company', '=', company],
            ['is_group', '=', 0],
          ]),
          limit_page_length: 100,
        },
      });
      setCostCenters(ccRes.data.data || []);
    } catch (error: any) {
      console.error('Error fetching accounts and cost centers:', error);
    }
  };

  const fetchMasterData = async () => {
    try {
      // Initial load of items (first 50) - auto-select first item if empty
      await searchItems('', true);

      // Initial load of companies (first 50) - auto-select first company if empty
      await searchCompanies('', true);

      // Fetch Asset Categories
      const catRes = await apiClient.get('/api/resource/Asset Category', {
        params: {
          fields: JSON.stringify(['name']),
          limit_page_length: 100,
        },
      });
      setAssetCategories(catRes.data.data || []);

      // Initial load of departments (first 50) - auto-select first department if empty
      await searchDepartments('', true);

      // Initial load of purchase receipts (first 50)
      await searchPurchaseReceipts();

      // Initial load of purchase invoices (first 50)
      await searchPurchaseInvoices();
      
      // Fetch accounts and cost centers for default company
      if (formData.company) {
        await fetchAccountsAndCostCenters(formData.company);
      }


    } catch (error: any) {
      toast({
        title: 'Error loading data',
        description: error.message,
        status: 'error',
        duration: 5000,
      });
    }
  };

  const fetchAssetCategoryAccounts = async (assetCategory: string, company?: string) => {
    const companyToUse = company || formData.company;
    if (!assetCategory || !companyToUse) return;
    
    try {
      const response = await apiClient.get(
        `/api/method/hkm.erpnext___custom.doctype.hkm_asset.hkm_asset.get_asset_category_accounts`,
        {
          params: {
            asset_category: assetCategory,
            company: companyToUse,
          },
        }
      );
      
      if (response.data.message) {
        const accounts = response.data.message;
        setFormData((prev) => ({
          ...prev,
          fixed_asset_account: accounts.fixed_asset_account || prev.fixed_asset_account,
          accumulated_depreciation_account: accounts.accumulated_depreciation_account || prev.accumulated_depreciation_account,
          depreciation_expense_account: accounts.depreciation_expense_account || prev.depreciation_expense_account,
          cwip_account: accounts.capital_work_in_progress_account || prev.cwip_account,
        }));
      }
    } catch (error: any) {
      console.error('Error fetching asset category accounts:', error);
    }
  };

  const fetchAssetSpecifications = async (assetCategory: string) => {
    if (!assetCategory) {
      setAssetSpecifications([]);
      setFormData((prev) => ({ ...prev, asset_specifications: [] }));
      return;
    }
    
    try {
      const response = await apiClient.get('/api/resource/HKM Asset Specification', {
        params: {
          fields: JSON.stringify(['name', 'specification_name', 'data_type', 'is_mandatory', 'options']),
          filters: JSON.stringify([['asset_category', '=', assetCategory]]),
          limit_page_length: 100,
        },
      });
      
      const specs = response.data.data || [];
      setAssetSpecifications(specs);
      
      // Initialize specifications in form data
      setFormData((prev) => ({
        ...prev,
        asset_specifications: specs.map((spec: any) => ({
          specification: spec.name,
          specification_name: spec.specification_name,
          data_type: spec.data_type,
          options: spec.options || '',
          value: spec.data_type === 'Checkbox' ? 'False' : '',
        })),
      }));
    } catch (error: any) {
      console.error('Error fetching asset specifications:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.item_code || !formData.custodian_department || !formData.purchase_date) {
      toast({
        title: 'Validation Error',
        description: 'Please fill all required fields',
        status: 'error',
        duration: 3000,
      });
      return;
    }

    // Validate mandatory specifications
    const missingSpecs = assetSpecifications
      .filter((spec, index) => {
        const specValue = formData.asset_specifications[index]?.value;
        // For checkbox, False is considered empty for mandatory fields
        if (spec.is_mandatory) {
          if (spec.data_type === 'Checkbox') {
            return specValue !== 'True';
          }
          return !specValue || specValue.trim() === '';
        }
        return false;
      })
      .map((spec) => spec.specification_name);

    if (missingSpecs.length > 0) {
      toast({
        title: 'Validation Error',
        description: `Please fill mandatory specifications: ${missingSpecs.join(', ')}`,
        status: 'error',
        duration: 5000,
      });
      return;
    }

    setLoading(true);
    try {
      // Prepare asset specifications for submission
      const assetSpecsData = formData.asset_specifications
        .filter((spec) => {
          // Include all mandatory specs, and non-mandatory specs that have values
          const specDef = assetSpecifications.find((s) => s.name === spec.specification);
          if (specDef?.is_mandatory) {
            return true; // Always include mandatory specs
          }
          // For checkbox, include if True, for others include if has value
          if (spec.data_type === 'Checkbox') {
            return spec.value === 'True';
          }
          return spec.value && spec.value.trim() !== '';
        })
        .map((spec) => ({
          specification: spec.specification,
          specification_name: spec.specification_name,
          value: spec.value || (spec.data_type === 'Checkbox' ? 'False' : ''),
        }));

      // Prepare submission data - remove empty strings and zero values for optional fields
      const submissionData: any = {
        naming_series: 'HKM-ASS-.YYYY.-',
        item_code: formData.item_code,
        asset_name: formData.asset_name,
        asset_category: formData.asset_category,
        company: formData.company,
        custodian_department: formData.custodian_department,
        purchase_date: formData.purchase_date,
        available_for_use_date: formData.available_for_use_date,
        gross_purchase_amount: formData.gross_purchase_amount,
        asset_quantity: formData.asset_quantity,
        calculate_depreciation: formData.calculate_depreciation ? 1 : 0,
        is_existing_asset: formData.is_existing_asset ? 1 : 0,
        maintenance_required: formData.maintenance_required ? 1 : 0,
      };

      // Add optional fields only if they have values
      if (formData.location) submissionData.location = formData.location;
      if (formData.sub_custodian) submissionData.sub_custodian = formData.sub_custodian;
      if (formData.purchase_receipt) submissionData.purchase_receipt = formData.purchase_receipt;
      if (formData.purchase_invoice) submissionData.purchase_invoice = formData.purchase_invoice;
      if (formData.cost_center) submissionData.cost_center = formData.cost_center;
      if (formData.remarks) submissionData.remarks = formData.remarks;

      // Depreciation fields
      if (formData.calculate_depreciation) {
        submissionData.depreciation_method = formData.depreciation_method;
        submissionData.frequency_of_depreciation = formData.frequency_of_depreciation;
        submissionData.total_number_of_depreciations = formData.total_number_of_depreciations;
        if (formData.depreciation_start_date) submissionData.depreciation_start_date = formData.depreciation_start_date;
        if (formData.expected_value_after_useful_life) submissionData.expected_value_after_useful_life = formData.expected_value_after_useful_life;
        
        // Opening depreciation fields for existing assets
        if (formData.is_existing_asset) {
          submissionData.opening_accumulated_depreciation = formData.opening_accumulated_depreciation || 0;
          submissionData.opening_number_of_booked_depreciations = formData.opening_number_of_booked_depreciations || 0;
        }
      }
      
      // Clear purchase receipt/invoice for existing assets (backend validation)
      if (formData.is_existing_asset) {
        submissionData.purchase_receipt = '';
        submissionData.purchase_invoice = '';
      }

      // Accounting fields
      if (formData.fixed_asset_account) submissionData.fixed_asset_account = formData.fixed_asset_account;
      if (formData.accumulated_depreciation_account) submissionData.accumulated_depreciation_account = formData.accumulated_depreciation_account;
      if (formData.depreciation_expense_account) submissionData.depreciation_expense_account = formData.depreciation_expense_account;
      if (formData.cwip_account) submissionData.cwip_account = formData.cwip_account;

      // Insurance fields
      if (formData.policy_number) submissionData.policy_number = formData.policy_number;
      if (formData.insurer) submissionData.insurer = formData.insurer;
      if (formData.insured_value) submissionData.insured_value = formData.insured_value;
      if (formData.insurance_start_date) submissionData.insurance_start_date = formData.insurance_start_date;
      if (formData.insurance_end_date) submissionData.insurance_end_date = formData.insurance_end_date;

      // Asset specifications
      if (assetSpecsData.length > 0) {
        submissionData.asset_specifications = assetSpecsData;
      }

      const response = await apiClient.post('/api/resource/HKM Asset', submissionData);

      toast({
        title: 'Asset Created!',
        description: `Asset ${response.data.data.name} created successfully`,
        status: 'success',
        duration: 5000,
      });

      navigate('/asset-dashboard/list');
    } catch (error: any) {
      toast({
        title: 'Error creating asset',
        description: error.response?.data?.message || error.message,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field: string, value: any) => {
    setFormData((prev) => {
      const updated = { ...prev, [field]: value };
      
      // Auto-fill asset_category and asset_name when item_code changes
      if (field === 'item_code') {
        const selectedOption = itemOptions.find((opt) => opt.value === value);
        if (selectedOption) {
          // Fetch full item details to get asset_category
          apiClient.get(`/api/resource/Item/${value}`, {
            params: {
              fields: JSON.stringify(['item_name', 'asset_category']),
            },
          }).then((response) => {
            const item = response.data.data;
            if (item) {
              setFormData((prev) => {
                const updated = { ...prev };
                if (item.item_name) updated.asset_name = item.item_name;
                if (item.asset_category) {
                  updated.asset_category = item.asset_category;
                  fetchAssetCategoryAccounts(item.asset_category, updated.company);
                  fetchAssetSpecifications(item.asset_category);
                }
                return updated;
              });
            }
          }).catch((error) => {
            console.error('Error fetching item details:', error);
          });
        }
      }
      
      // Fetch accounts when asset_category changes
      if (field === 'asset_category' && value) {
        fetchAssetCategoryAccounts(value, updated.company);
        fetchAssetSpecifications(value);
      }
      
      // Fetch accounts and cost centers when company changes
      if (field === 'company' && value) {
        fetchAccountsAndCostCenters(value);
        // Re-fetch asset category accounts with new company if asset category is set
        if (updated.asset_category) {
          fetchAssetCategoryAccounts(updated.asset_category, value);
        }
      }
      
      return updated;
    });
  };

  const handleSpecificationChange = (index: number, value: string | boolean) => {
    setFormData((prev) => {
      const updated = [...prev.asset_specifications];
      const spec = updated[index];
      
      // For checkbox, convert boolean to "True" or "False" string
      if (spec.data_type === 'Checkbox') {
        updated[index] = { ...spec, value: value ? 'True' : 'False' };
      } else {
        updated[index] = { ...spec, value: value as string };
      }
      
      return { ...prev, asset_specifications: updated };
    });
  };

  return (
    <Box minH="100vh" bg="gray.50">
      <PageHeader
        title="Create New Asset"
        subtitle="Register a new asset with purchase and depreciation details"
        backTo="/asset-dashboard"
      />

      <Container maxW="container.lg" py={8}>
        <Box as="form" onSubmit={handleSubmit} bg="white" p={8} borderRadius="xl" shadow="md">
          <VStack spacing={6} align="stretch">
            {/* Basic Information */}
            <Box>
              <Heading size="md" mb={4}>Basic Information</Heading>
              <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                <FormControl isRequired>
                  <FormLabel>Item Code</FormLabel>
                  <SearchableSelect
                    options={itemOptions}
                    value={formData.item_code}
                    onChange={(value) => handleChange('item_code', value)}
                    onSearch={handleItemSearch}
                    isLoading={isSearchingItems}
                    placeholder="Search and select fixed asset item"
                    size="md"
                    emptyMessage="No items found"
                  />
                </FormControl>

                <FormControl>
                  <FormLabel>Asset Name</FormLabel>
                  <Input
                    value={formData.asset_name}
                    onChange={(e) => handleChange('asset_name', e.target.value)}
                    placeholder="Enter asset name"
                  />
                </FormControl>

                <FormControl>
                  <FormLabel>Asset Category</FormLabel>
                  <Input
                    value={formData.asset_category}
                    isReadOnly
                    bg="gray.50"
                    placeholder="Auto-filled from item"
                  />
                </FormControl>

                <FormControl isRequired>
                  <FormLabel>Company</FormLabel>
                  <SearchableSelect
                    options={companyOptions}
                    value={formData.company}
                    onChange={(value) => handleChange('company', value)}
                    onSearch={handleCompanySearch}
                    isLoading={isSearchingCompanies}
                    placeholder="Search and select company"
                    size="md"
                    emptyMessage="No companies found"
                  />
                </FormControl>

                <FormControl isRequired>
                  <FormLabel>Custodian Department</FormLabel>
                  <SearchableSelect
                    options={departmentOptions}
                    value={formData.custodian_department}
                    onChange={(value) => handleChange('custodian_department', value)}
                    onSearch={handleDepartmentSearch}
                    isLoading={isSearchingDepartments}
                    placeholder="Search and select department"
                    size="md"
                  />
                </FormControl>

                <FormControl>
                  <FormLabel>Location</FormLabel>
                  <Input
                    value={formData.location}
                    onChange={(e) => handleChange('location', e.target.value)}
                    placeholder="Enter location"
                  />
                </FormControl>

                <FormControl>
                  <FormLabel>Sub Custodian</FormLabel>
                  <Input
                    value={formData.sub_custodian}
                    onChange={(e) => handleChange('sub_custodian', e.target.value)}
                    placeholder="Enter sub custodian name"
                  />
                </FormControl>

                <FormControl>
                  <Checkbox
                    isChecked={formData.is_existing_asset}
                    onChange={(e) => handleChange('is_existing_asset', e.target.checked)}
                  >
                    Is Existing Asset
                  </Checkbox>
                </FormControl>
              </SimpleGrid>
            </Box>

            <Divider />

            {/* Purchase Details */}
            <Box>
              <Heading size="md" mb={4}>Purchase Details</Heading>
              <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                <FormControl isDisabled={formData.is_existing_asset}>
                  <FormLabel>Purchase Receipt</FormLabel>
                  <SearchableSelect
                    options={purchaseReceiptOptions}
                    value={formData.purchase_receipt}
                    onChange={(value) => handleChange('purchase_receipt', value)}
                    onSearch={handlePurchaseReceiptSearch}
                    isLoading={isSearchingPurchaseReceipts}
                    placeholder="Search and select purchase receipt (optional)"
                    size="md"
                    isDisabled={formData.is_existing_asset}
                  />
                  {formData.is_existing_asset && (
                    <Text fontSize="xs" color="gray.500" mt={1}>
                      Not applicable for existing assets
                    </Text>
                  )}
                </FormControl>

                <FormControl isDisabled={formData.is_existing_asset}>
                  <FormLabel>Purchase Invoice</FormLabel>
                  <SearchableSelect
                    options={purchaseInvoiceOptions}
                    value={formData.purchase_invoice}
                    onChange={(value) => handleChange('purchase_invoice', value)}
                    onSearch={handlePurchaseInvoiceSearch}
                    isLoading={isSearchingPurchaseInvoices}
                    placeholder="Search and select purchase invoice (optional)"
                    size="md"
                    isDisabled={formData.is_existing_asset}
                  />
                  {formData.is_existing_asset && (
                    <Text fontSize="xs" color="gray.500" mt={1}>
                      Not applicable for existing assets
                    </Text>
                  )}
                </FormControl>

                <FormControl isRequired>
                  <FormLabel>Purchase Date</FormLabel>
                  <Input
                    type="date"
                    value={formData.purchase_date}
                    onChange={(e) => handleChange('purchase_date', e.target.value)}
                  />
                </FormControl>

                <FormControl isRequired>
                  <FormLabel>Available for Use Date</FormLabel>
                  <Input
                    type="date"
                    value={formData.available_for_use_date}
                    onChange={(e) => handleChange('available_for_use_date', e.target.value)}
                  />
                </FormControl>

                <FormControl isRequired>
                  <FormLabel>Gross Purchase Amount (₹)</FormLabel>
                  <NumberInput
                    value={formData.gross_purchase_amount}
                    onChange={(_, value) => handleChange('gross_purchase_amount', value)}
                  >
                    <NumberInputField />
                  </NumberInput>
                </FormControl>

                <FormControl>
                  <FormLabel>Asset Quantity</FormLabel>
                  <NumberInput
                    value={formData.asset_quantity}
                    onChange={(_, value) => handleChange('asset_quantity', value)}
                    min={1}
                  >
                    <NumberInputField />
                  </NumberInput>
                </FormControl>
              </SimpleGrid>
            </Box>

            <Divider />

            {/* Depreciation Settings */}
            <Box>
              <Heading size="md" mb={4}>Depreciation Settings</Heading>
              <VStack align="stretch" spacing={4}>
                <Checkbox
                  isChecked={formData.calculate_depreciation}
                  onChange={(e) => handleChange('calculate_depreciation', e.target.checked)}
                >
                  Calculate Depreciation
                </Checkbox>

                <Collapse in={formData.calculate_depreciation} animateOpacity>
                  <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                    <FormControl>
                      <FormLabel>Depreciation Method</FormLabel>
                      <Input
                        value={formData.depreciation_method}
                        isReadOnly
                        bg="gray.50"
                      />
                    </FormControl>

                    <FormControl>
                      <FormLabel>Frequency (months)</FormLabel>
                      <NumberInput
                        value={formData.frequency_of_depreciation}
                        onChange={(_, value) => handleChange('frequency_of_depreciation', value)}
                      >
                        <NumberInputField />
                      </NumberInput>
                      <Text fontSize="xs" color="gray.500">12 = Monthly</Text>
                    </FormControl>

                    <FormControl>
                      <FormLabel>Total Depreciations</FormLabel>
                      <NumberInput
                        value={formData.total_number_of_depreciations}
                        onChange={(_, value) => handleChange('total_number_of_depreciations', value)}
                      >
                        <NumberInputField />
                      </NumberInput>
                      <Text fontSize="xs" color="gray.500">60 = 5 years (monthly)</Text>
                    </FormControl>

                    <FormControl>
                      <FormLabel>Depreciation Start Date</FormLabel>
                      <Input
                        type="date"
                        value={formData.depreciation_start_date}
                        onChange={(e) => handleChange('depreciation_start_date', e.target.value)}
                      />
                    </FormControl>

                    <FormControl>
                      <FormLabel>Expected Salvage Value (₹)</FormLabel>
                      <NumberInput
                        value={formData.expected_value_after_useful_life}
                        onChange={(_, value) => handleChange('expected_value_after_useful_life', value)}
                      >
                        <NumberInputField />
                      </NumberInput>
                    </FormControl>
                  </SimpleGrid>
                </Collapse>

                <Collapse in={formData.is_existing_asset && formData.calculate_depreciation} animateOpacity>
                  <Box mt={4} p={4} bg="blue.50" borderRadius="md">
                    <Heading size="sm" mb={3}>Opening Depreciation Details</Heading>
                    <Text fontSize="sm" color="gray.600" mb={4}>
                      For existing assets, optionally enter the accumulated depreciation and number of depreciations already booked.
                    </Text>
                    <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                      <FormControl>
                        <FormLabel>Opening Accumulated Depreciation (₹)</FormLabel>
                        <NumberInput
                          value={formData.opening_accumulated_depreciation}
                          onChange={(_, value) => handleChange('opening_accumulated_depreciation', value || 0)}
                          min={0}
                        >
                          <NumberInputField />
                        </NumberInput>
                      </FormControl>

                      <FormControl>
                        <FormLabel>Opening Number of Booked Depreciations</FormLabel>
                        <NumberInput
                          value={formData.opening_number_of_booked_depreciations}
                          onChange={(_, value) => handleChange('opening_number_of_booked_depreciations', value || 0)}
                          min={0}
                        >
                          <NumberInputField />
                        </NumberInput>
                        {formData.opening_accumulated_depreciation > 0 && formData.opening_number_of_booked_depreciations === 0 && (
                          <Text fontSize="xs" color="orange.500" mt={1}>
                            Recommended: Set this when opening accumulated depreciation is provided
                          </Text>
                        )}
                      </FormControl>
                    </SimpleGrid>
                  </Box>
                </Collapse>
              </VStack>
            </Box>

            <Divider />

            {/* Accounting */}
            <Box>
              <Heading size="md" mb={4}>Accounting</Heading>
              <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                <FormControl>
                  <FormLabel>Fixed Asset Account</FormLabel>
                  <Select
                    value={formData.fixed_asset_account}
                    onChange={(e) => handleChange('fixed_asset_account', e.target.value)}
                    placeholder="Select fixed asset account"
                  >
                    <option value="">None</option>
                    {accounts
                      .filter((acc) => acc.account_type === 'Fixed Asset')
                      .map((acc) => (
                        <option key={acc.name} value={acc.name}>
                          {acc.name} - {acc.account_name}
                        </option>
                      ))}
                  </Select>
                </FormControl>

                <FormControl>
                  <FormLabel>Accumulated Depreciation Account</FormLabel>
                  <Select
                    value={formData.accumulated_depreciation_account}
                    onChange={(e) => handleChange('accumulated_depreciation_account', e.target.value)}
                    placeholder="Select accumulated depreciation account"
                  >
                    <option value="">None</option>
                    {accounts
                      .filter((acc) => acc.account_type === 'Accumulated Depreciation')
                      .map((acc) => (
                        <option key={acc.name} value={acc.name}>
                          {acc.name} - {acc.account_name}
                        </option>
                      ))}
                  </Select>
                </FormControl>

                <Collapse in={formData.calculate_depreciation} animateOpacity>
                  <FormControl>
                    <FormLabel>Depreciation Expense Account</FormLabel>
                    <Select
                      value={formData.depreciation_expense_account}
                      onChange={(e) => handleChange('depreciation_expense_account', e.target.value)}
                      placeholder="Select depreciation expense account"
                    >
                      <option value="">None</option>
                      {accounts
                        .filter((acc) => acc.account_type === 'Depreciation')
                        .map((acc) => (
                          <option key={acc.name} value={acc.name}>
                            {acc.name} - {acc.account_name}
                          </option>
                        ))}
                    </Select>
                  </FormControl>
                </Collapse>

                <FormControl>
                  <FormLabel>CWIP Account</FormLabel>
                  <Select
                    value={formData.cwip_account}
                    onChange={(e) => handleChange('cwip_account', e.target.value)}
                    placeholder="Select CWIP account"
                  >
                    <option value="">None</option>
                    {accounts
                      .filter((acc) => acc.account_type === 'Capital Work in Progress')
                      .map((acc) => (
                        <option key={acc.name} value={acc.name}>
                          {acc.name} - {acc.account_name}
                        </option>
                      ))}
                  </Select>
                </FormControl>

                <FormControl>
                  <FormLabel>Cost Center</FormLabel>
                  <Select
                    value={formData.cost_center}
                    onChange={(e) => handleChange('cost_center', e.target.value)}
                    placeholder="Select cost center"
                  >
                    <option value="">None</option>
                    {costCenters.map((cc) => (
                      <option key={cc.name} value={cc.name}>
                        {cc.name} - {cc.cost_center_name}
                      </option>
                    ))}
                  </Select>
                </FormControl>
              </SimpleGrid>
            </Box>

            <Divider />

            {/* Insurance Details */}
            <Box>
              <Heading size="md" mb={4}>Insurance Details</Heading>
              <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                <FormControl>
                  <FormLabel>Policy Number</FormLabel>
                  <Input
                    value={formData.policy_number}
                    onChange={(e) => handleChange('policy_number', e.target.value)}
                    placeholder="Enter policy number"
                  />
                </FormControl>

                <FormControl>
                  <FormLabel>Insurer</FormLabel>
                  <Input
                    value={formData.insurer}
                    onChange={(e) => handleChange('insurer', e.target.value)}
                    placeholder="Enter insurer name"
                  />
                </FormControl>

                <FormControl>
                  <FormLabel>Insured Value (₹)</FormLabel>
                  <NumberInput
                    value={formData.insured_value}
                    onChange={(_, value) => handleChange('insured_value', value)}
                  >
                    <NumberInputField />
                  </NumberInput>
                </FormControl>

                <FormControl>
                  <FormLabel>Insurance Start Date</FormLabel>
                  <Input
                    type="date"
                    value={formData.insurance_start_date}
                    onChange={(e) => handleChange('insurance_start_date', e.target.value)}
                  />
                </FormControl>

                <FormControl>
                  <FormLabel>Insurance End Date</FormLabel>
                  <Input
                    type="date"
                    value={formData.insurance_end_date}
                    onChange={(e) => handleChange('insurance_end_date', e.target.value)}
                  />
                </FormControl>
              </SimpleGrid>
            </Box>

            <Divider />

            {/* Asset Specifications */}
            {assetSpecifications.length > 0 && (
              <Box>
                <Heading size="md" mb={4}>Asset Specifications</Heading>
                <VStack spacing={4} align="stretch">
                  {assetSpecifications.map((spec, index) => {
                    const specData = formData.asset_specifications[index];
                    const currentValue = specData?.value || '';
                    
                    return (
                      <FormControl key={spec.name} isRequired={spec.is_mandatory}>
                        {spec.data_type === 'Checkbox' ? (
                          <>
                            <Checkbox
                              isChecked={currentValue === 'True'}
                              onChange={(e) => handleSpecificationChange(index, e.target.checked)}
                            >
                              {spec.specification_name}
                              {spec.is_mandatory && <Text as="span" color="red.500"> *</Text>}
                            </Checkbox>
                          </>
                        ) : (
                          <>
                            <FormLabel>
                              {spec.specification_name}
                              {spec.is_mandatory && <Text as="span" color="red.500"> *</Text>}
                            </FormLabel>
                            {spec.data_type === 'Select' ? (
                              <Select
                                value={currentValue}
                                onChange={(e) => handleSpecificationChange(index, e.target.value)}
                                placeholder={`Select ${spec.specification_name.toLowerCase()}`}
                              >
                                {!spec.is_mandatory && <option value="">None</option>}
                                {specData?.options
                                  ?.split(',')
                                  .map((opt: string) => opt.trim())
                                  .filter((opt: string) => opt)
                                  .map((opt: string) => (
                                    <option key={opt} value={opt}>
                                      {opt}
                                    </option>
                                  ))}
                              </Select>
                            ) : spec.data_type === 'Date' ? (
                              <Input
                                type="date"
                                value={currentValue}
                                onChange={(e) => handleSpecificationChange(index, e.target.value)}
                                placeholder={`Select ${spec.specification_name.toLowerCase()}`}
                              />
                            ) : spec.data_type === 'Number' ? (
                              <NumberInput
                                value={currentValue && !isNaN(parseFloat(currentValue)) ? parseFloat(currentValue) : undefined}
                                onChange={(_, value) => handleSpecificationChange(index, value !== undefined && !isNaN(value) ? value.toString() : '')}
                              >
                                <NumberInputField placeholder={`Enter ${spec.specification_name.toLowerCase()}`} />
                              </NumberInput>
                            ) : (
                              <Input
                                value={currentValue}
                                onChange={(e) => handleSpecificationChange(index, e.target.value)}
                                placeholder={`Enter ${spec.specification_name.toLowerCase()}`}
                                type="text"
                              />
                            )}
                          </>
                        )}
                      </FormControl>
                    );
                  })}
                </VStack>
              </Box>
            )}

            <Divider />

            {/* Other Details */}
            <Box>
              <Heading size="md" mb={4}>Other Details</Heading>
              <VStack align="stretch" spacing={4}>
                <FormControl>
                  <Checkbox
                    isChecked={formData.maintenance_required}
                    onChange={(e) => handleChange('maintenance_required', e.target.checked)}
                  >
                    Maintenance Required
                  </Checkbox>
                </FormControl>

                <FormControl>
                  <FormLabel>Remarks</FormLabel>
                  <Textarea
                    value={formData.remarks}
                    onChange={(e) => handleChange('remarks', e.target.value)}
                    placeholder="Any additional notes..."
                    rows={4}
                  />
                </FormControl>
              </VStack>
            </Box>

            {/* Actions */}
            <HStack spacing={4} justify="flex-end">
              <Button
                leftIcon={<FiArrowLeft />}
                variant="outline"
                onClick={() => navigate('/asset-dashboard')}
              >
                Cancel
              </Button>
              <Button
                leftIcon={<FiSave />}
                colorScheme="green"
                type="submit"
                isLoading={loading}
              >
                Create Asset
              </Button>
            </HStack>
          </VStack>
        </Box>
      </Container>
    </Box>
  );
};

export default CreateAssetPage;



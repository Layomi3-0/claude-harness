# React Component Guidelines

Clean, maintainable React components that are easy to read, test, and modify.

---

## Core Principles

### 1. Components Should Be Small

**Target: 50-150 lines max.** If a component exceeds 200 lines, it needs splitting.

```tsx
// BAD: 600-line OrderForm with validation, steps, and all renders
function OrderForm() {
  // 50 lines of state
  // 100 lines of validation
  // 400 lines of JSX for 4 steps
}

// GOOD: Composed from focused components
function OrderForm() {
  const form = useOrderForm();

  return (
    <FormContainer>
      <StepIndicator current={form.step} steps={ORDER_STEPS} />
      <OrderFormStep {...form} />
      <FormNavigation {...form} />
    </FormContainer>
  );
}
```

### 2. Separate Concerns

Split components by responsibility:

| Concern | Location | Example |
|---------|----------|---------|
| Data fetching | Custom hooks | `useOrder()` |
| Business logic | Custom hooks | `useOrderForm()` |
| Validation | Separate files | `validators/order.ts` |
| Constants/config | Separate files | `constants/order.ts` |
| Presentation | Components | `OrderStepProducts.tsx` |

### 3. Logic Up, Presentation Down

Parent components handle logic. Child components render UI.

```tsx
// Parent: handles data and logic
function OrderPage() {
  const order = useOrder(orderId);
  const handleCancel = () => { /* logic */ };

  return <OrderDetails order={order} onCancel={handleCancel} />;
}

// Child: pure presentation
function OrderDetails({ order, onCancel }: OrderDetailsProps) {
  return (
    <Card>
      <OrderHeader order={order} />
      <OrderItems items={order.items} />
      <Button onClick={onCancel}>Cancel</Button>
    </Card>
  );
}
```

---

## File Structure

```
components/
├── ui/                     # Reusable primitives (Button, Card, Input)
├── icons/                  # SVG icon components
├── order/
│   ├── OrderForm/
│   │   ├── index.tsx       # Main export, composes sub-components
│   │   ├── OrderFormStep.tsx
│   │   ├── StepProducts.tsx
│   │   ├── StepContact.tsx
│   │   ├── StepShipping.tsx
│   │   ├── StepReview.tsx
│   │   └── useOrderForm.ts # Form logic hook
│   ├── OrderTable.tsx
│   └── OrderStatusCard.tsx
├── admin/
│   └── ...
└── shared/                 # Cross-feature components
    ├── StepIndicator.tsx
    ├── DataRow.tsx
    └── EmptyState.tsx
```

### Naming Conventions

- **Components**: PascalCase (`OrderForm.tsx`)
- **Hooks**: camelCase with `use` prefix (`useOrderForm.ts`)
- **Constants**: SCREAMING_SNAKE_CASE (`ORDER_STEPS`)
- **Types**: PascalCase with descriptive suffix (`OrderFormProps`, `OrderItem`)

---

## Component Patterns

### Pattern 1: Container/Presenter Split

**Container**: Fetches data, handles logic, passes props down.

```tsx
// OrderFormContainer.tsx (or just use the page component)
export function OrderFormContainer() {
  const form = useOrderForm();
  const { mutate: createOrder, isPending } = useCreateOrder();

  const handleSubmit = async (data: OrderFormData) => {
    await createOrder(data);
  };

  return (
    <OrderForm
      step={form.step}
      data={form.data}
      errors={form.errors}
      onStepChange={form.setStep}
      onFieldChange={form.updateField}
      onSubmit={handleSubmit}
      isSubmitting={isPending}
    />
  );
}
```

**Presenter**: Pure rendering, no side effects.

```tsx
// OrderForm.tsx
interface OrderFormProps {
  step: number;
  data: OrderFormData;
  errors: Record<string, string>;
  onStepChange: (step: number) => void;
  onFieldChange: (field: string, value: unknown) => void;
  onSubmit: () => void;
  isSubmitting: boolean;
}

export function OrderForm({
  step,
  data,
  errors,
  onStepChange,
  onFieldChange,
  onSubmit,
  isSubmitting,
}: OrderFormProps) {
  return (
    <Card>
      <StepIndicator current={step} steps={ORDER_STEPS} />
      <CurrentStep step={step} data={data} errors={errors} onChange={onFieldChange} />
      <FormNavigation
        step={step}
        totalSteps={ORDER_STEPS.length}
        onBack={() => onStepChange(step - 1)}
        onNext={() => onStepChange(step + 1)}
        onSubmit={onSubmit}
        isSubmitting={isSubmitting}
      />
    </Card>
  );
}
```

### Pattern 2: Compound Components

For complex UI with related parts:

```tsx
// Usage
<DataList>
  <DataList.Item label="Name" value={customer.name} />
  <DataList.Item label="Email" value={customer.email} />
  <DataList.Item label="Phone" value={customer.phone} />
</DataList>

// Implementation
export function DataList({ children }: { children: React.ReactNode }) {
  return <div className="space-y-2">{children}</div>;
}

function DataListItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between text-sm">
      <span className="text-[var(--text-tertiary)]">{label}</span>
      <span className="text-[var(--text-primary)] font-medium">{value}</span>
    </div>
  );
}

DataList.Item = DataListItem;
```

### Pattern 3: Render Props for Flexibility

When children need parent data:

```tsx
<OrderItemList
  items={order.items}
  renderItem={(item) => (
    <OrderItemCard key={item.id} item={item} onRemove={() => removeItem(item.id)} />
  )}
  renderEmpty={() => <EmptyState message="No items yet" />}
/>
```

---

## Extracting Subcomponents

### When to Extract

Extract when you see:
- Repeated JSX patterns (3+ times)
- Conditional rendering blocks (>10 lines)
- Map callbacks (>5 lines)
- Self-contained UI sections

### Before: Inline Everything

```tsx
function OrderForm() {
  return (
    <div>
      {/* Progress - 50 lines of JSX */}
      <div className="flex items-start">
        {[
          { num: 1, label: "Products" },
          { num: 2, label: "Contact" },
          { num: 3, label: "Shipping" },
          { num: 4, label: "Review" },
        ].map((s, index) => (
          <div key={s.num} className="flex-1 flex flex-col items-center">
            <div className="flex items-center w-full">
              <div
                className="flex-1 h-1 rounded-full transition-all duration-500"
                style={{ background: index === 0 ? "transparent" : ... }}
              />
              {/* ... 30 more lines */}
            </div>
          </div>
        ))}
      </div>

      {/* Form content - 400 more lines */}
    </div>
  );
}
```

### After: Extracted Component

```tsx
// StepIndicator.tsx
const STEP_LABELS = ["Products", "Contact", "Shipping", "Review"] as const;

interface StepIndicatorProps {
  currentStep: number;
  steps?: readonly string[];
}

export function StepIndicator({ currentStep, steps = STEP_LABELS }: StepIndicatorProps) {
  return (
    <div className="flex items-start mb-8">
      {steps.map((label, index) => (
        <StepIndicatorItem
          key={label}
          step={index + 1}
          label={label}
          isActive={index + 1 <= currentStep}
          isFirst={index === 0}
          isLast={index === steps.length - 1}
        />
      ))}
    </div>
  );
}

function StepIndicatorItem({ step, label, isActive, isFirst, isLast }: StepIndicatorItemProps) {
  return (
    <div className="flex-1 flex flex-col items-center">
      {/* Clean, focused JSX */}
    </div>
  );
}
```

---

## Custom Hooks

### Extract Logic Into Hooks

**Before**: Logic mixed with JSX

```tsx
function OrderForm() {
  const [step, setStep] = useState(1);
  const [items, setItems] = useState<OrderItem[]>([{ productUrl: "", quantity: 1 }]);
  const [customer, setCustomer] = useState<CustomerInfo>({ name: "", email: "", phone: "" });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const addItem = () => { /* ... */ };
  const removeItem = (index: number) => { /* ... */ };
  const updateItem = (index: number, field: string, value: unknown) => { /* ... */ };
  const validateStep = (step: number) => { /* 50 lines */ };
  const handleNext = () => { /* ... */ };
  const handleBack = () => { /* ... */ };

  // 400 lines of JSX...
}
```

**After**: Clean separation

```tsx
// useOrderForm.ts
export function useOrderForm() {
  const [step, setStep] = useState(1);
  const [data, setData] = useState<OrderFormData>(INITIAL_DATA);
  const [errors, setErrors] = useState<FormErrors>({});

  const updateField = useCallback((path: string, value: unknown) => {
    setData(prev => set(prev, path, value));
    setErrors(prev => omit(prev, path));
  }, []);

  const validateCurrentStep = useCallback(() => {
    const stepErrors = validateStep(step, data);
    setErrors(stepErrors);
    return Object.keys(stepErrors).length === 0;
  }, [step, data]);

  const goNext = useCallback(() => {
    if (validateCurrentStep()) setStep(s => s + 1);
  }, [validateCurrentStep]);

  const goBack = useCallback(() => {
    setStep(s => s - 1);
  }, []);

  return { step, data, errors, updateField, goNext, goBack, validateCurrentStep };
}

// OrderForm.tsx - now focused on rendering
function OrderForm() {
  const form = useOrderForm();

  return (
    <Card>
      <StepIndicator currentStep={form.step} />
      <OrderFormContent {...form} />
      <FormNavigation {...form} />
    </Card>
  );
}
```

### Hook Naming

```tsx
// Data fetching
useOrder(orderId)           // Single resource
useOrders(filters)          // Collection
useOrderMutation()          // Mutations

// Form state
useOrderForm()              // Form with validation
useMultiStepForm(steps)     // Generic multi-step

// UI state
useDisclosure()             // open/close state
useSteps(totalSteps)        // step navigation
```

---

## Icons

### Create Reusable Icon Components

**Don't**: Inline SVGs everywhere

```tsx
// BAD: Same SVG repeated 10 times across files
<svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
</svg>
```

**Do**: Create icon components

```tsx
// components/icons/index.tsx
interface IconProps {
  className?: string;
  size?: number;
}

export function CheckIcon({ className = "", size = 20 }: IconProps) {
  return (
    <svg
      className={className}
      width={size}
      height={size}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
    </svg>
  );
}

export function ChevronLeftIcon({ className = "", size = 20 }: IconProps) { /* ... */ }
export function ChevronRightIcon({ className = "", size = 20 }: IconProps) { /* ... */ }
export function PlusIcon({ className = "", size = 20 }: IconProps) { /* ... */ }
export function TrashIcon({ className = "", size = 20 }: IconProps) { /* ... */ }
// ... etc

// Usage
import { CheckIcon, ChevronRightIcon } from "@/components/icons";

<Button>
  Next <ChevronRightIcon className="ml-2" />
</Button>
```

---

## Styling

### Use Design Tokens

Always use CSS variables from the design system:

```tsx
// GOOD: Uses design tokens
<div style={{ color: "var(--text-primary)", background: "var(--bg-secondary)" }}>

// BAD: Hardcoded colors
<div className="text-gray-900 bg-gray-100">
```

### Prefer className Over Inline Styles

```tsx
// GOOD: Tailwind classes
<div className="rounded-xl p-4 bg-[var(--bg-tertiary)] border border-[var(--border-light)]">

// AVOID: Inline style objects (harder to read, no Tailwind benefits)
<div style={{ borderRadius: '0.75rem', padding: '1rem', background: 'var(--bg-tertiary)' }}>
```

### Extract Repeated Style Patterns

```tsx
// styles.ts or at top of component file
const cardStyles = "rounded-xl p-4 bg-[var(--bg-tertiary)] border border-[var(--border-light)]";
const labelStyles = "text-sm font-medium text-[var(--text-secondary)]";

// Usage
<div className={cardStyles}>
  <span className={labelStyles}>Label</span>
</div>
```

---

## Props

### Keep Props Minimal

```tsx
// BAD: Too many props, tight coupling
<OrderItem
  item={item}
  index={index}
  onRemove={removeItem}
  onUpdateQuantity={updateQuantity}
  onUpdateUrl={updateUrl}
  showRemoveButton={items.length > 1}
  errors={errors}
  isFirst={index === 0}
  isLast={index === items.length - 1}
/>

// GOOD: Focused props
<OrderItemRow
  item={item}
  errors={itemErrors}
  onUpdate={handleUpdate}
  onRemove={canRemove ? handleRemove : undefined}
/>
```

### Use Discriminated Unions for Variants

```tsx
// Instead of boolean props
type ButtonProps =
  | { variant: "primary"; onClick: () => void }
  | { variant: "link"; href: string }
  | { variant: "submit"; form: string };

// Usage is type-safe
<Button variant="link" href="/orders" />      // OK
<Button variant="link" onClick={fn} />        // Type error!
```

### Prefer Children Over Render Props

```tsx
// GOOD: Simple composition
<Card>
  <CardHeader>
    <CardTitle>Order Details</CardTitle>
  </CardHeader>
  <CardContent>
    {/* content */}
  </CardContent>
</Card>

// Use render props only when children need parent data
<AnimatedList items={items}>
  {(item, { isActive }) => <ListItem item={item} active={isActive} />}
</AnimatedList>
```

---

## Constants and Configuration

### Extract to Separate Files

```tsx
// constants/order.ts
export const ORDER_STEPS = [
  { id: 1, label: "Products", description: "Add product URLs" },
  { id: 2, label: "Contact", description: "Your contact info" },
  { id: 3, label: "Shipping", description: "Delivery address" },
  { id: 4, label: "Review", description: "Confirm order" },
] as const;

export const MAX_ORDER_ITEMS = 20;

export const INITIAL_ORDER_ITEM: OrderItem = {
  productUrl: "",
  quantity: 1,
};
```

### Extract Status Mappings

```tsx
// constants/status.ts
export const STATUS_CONFIG: Record<OrderStatus, StatusConfig> = {
  SUBMITTED: { label: "Submitted", variant: "default", icon: ClockIcon },
  SCRAPING: { label: "Processing", variant: "info", icon: RefreshIcon },
  QUOTE_READY: { label: "Quote Ready", variant: "success", icon: CheckIcon },
  // ...
};

// Usage
const config = STATUS_CONFIG[order.status];
<Badge variant={config.variant}>
  <config.icon className="w-4 h-4 mr-1" />
  {config.label}
</Badge>
```

---

## Validation

### Separate Validation Logic

```tsx
// validators/order.ts
import { z } from "zod";

export const customerSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  email: z.string().email("Invalid email format"),
  phone: z.string().min(10, "Phone must be at least 10 digits"),
  whatsapp: z.string().optional(),
});

export const orderItemSchema = z.object({
  productUrl: z.string().url("Invalid URL format"),
  quantity: z.number().min(1, "Quantity must be at least 1"),
});

export const shippingSchema = z.object({
  street: z.string().min(5, "Street must be at least 5 characters"),
  city: z.string().min(2, "City is required"),
  state: z.string().min(2, "State is required"),
  postalCode: z.string().optional(),
  country: z.string().default("NG"),
});

// In hook
export function useOrderForm() {
  const validateStep = (step: number): FormErrors => {
    const schema = [orderItemSchema, customerSchema, shippingSchema][step - 1];
    const result = schema.safeParse(data);
    return result.success ? {} : formatZodErrors(result.error);
  };
}
```

---

## Testing Considerations

Write components that are easy to test:

```tsx
// Testable: Pure function of props
function OrderSummary({ items, total }: OrderSummaryProps) {
  return (
    <div data-testid="order-summary">
      <span data-testid="item-count">{items.length} items</span>
      <span data-testid="total">{formatCurrency(total)}</span>
    </div>
  );
}

// Test
it("displays correct item count and total", () => {
  render(<OrderSummary items={mockItems} total={100} />);
  expect(screen.getByTestId("item-count")).toHaveTextContent("3 items");
  expect(screen.getByTestId("total")).toHaveTextContent("$100.00");
});
```

---

## Quick Reference Checklist

Before committing a component, verify:

- [ ] **Size**: Under 150 lines? If not, can it be split?
- [ ] **Single Responsibility**: Does it do one thing well?
- [ ] **Props**: Minimal and focused? No boolean soup?
- [ ] **Logic**: Extracted to hooks? No inline validation?
- [ ] **Icons**: Using icon components, not inline SVGs?
- [ ] **Constants**: Extracted to separate files?
- [ ] **Styles**: Using design tokens? Tailwind over inline styles?
- [ ] **Types**: Props interface defined? No `any` types?

---

## Migration Strategy

When refactoring existing large components:

1. **Extract constants first** - Move data arrays, config objects
2. **Extract icons** - Replace inline SVGs with icon components
3. **Extract hooks** - Move state and logic to custom hooks
4. **Split by section** - Extract major JSX sections as subcomponents
5. **Test each step** - Ensure behavior unchanged after each extraction

Example migration order for `OrderForm.tsx`:
1. Extract `ORDER_STEPS` constant
2. Create icon components for all inline SVGs
3. Extract `useOrderForm` hook with all state/validation
4. Extract `StepIndicator` component
5. Extract `StepProducts`, `StepContact`, `StepShipping`, `StepReview`
6. Extract `FormNavigation` component
7. Compose in main `OrderForm`

---

*Remember: The goal is code that reads like well-written prose and looks like it was written by someone who cares.*

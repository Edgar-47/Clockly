import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/app_colors.dart';
import '../../../shared/extensions/context_extensions.dart';
import '../../../shared/widgets/app_button.dart';
import '../../../shared/widgets/app_text_field.dart';
import '../providers/tickets_provider.dart';

class CreateTicketScreen extends ConsumerStatefulWidget {
  const CreateTicketScreen({super.key});

  @override
  ConsumerState<CreateTicketScreen> createState() => _CreateTicketScreenState();
}

class _CreateTicketScreenState extends ConsumerState<CreateTicketScreen> {
  final _formKey = GlobalKey<FormState>();
  final _titleController = TextEditingController();
  final _amountController = TextEditingController();
  final _descriptionController = TextEditingController();
  String _category = 'expense';
  DateTime _date = DateTime.now();

  @override
  void dispose() {
    _titleController.dispose();
    _amountController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    final amount = double.tryParse(_amountController.text.replaceAll(',', '.'));
    if (amount == null) {
      context.showSnackBar('Introduce un importe válido', isError: true);
      return;
    }
    final ok = await ref.read(ticketsProvider.notifier).createTicket(
          title: _titleController.text.trim(),
          amount: amount,
          category: _category,
          date: _date,
          description: _descriptionController.text.trim(),
        );
    if (ok && mounted) {
      context.showSnackBar('Ticket creado correctamente');
      context.pop();
    }
  }

  @override
  Widget build(BuildContext context) {
    final isLoading =
        ref.watch(ticketsProvider).valueOrNull?.actionLoading ?? false;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Nuevo ticket'),
        centerTitle: false,
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(24),
          children: [
            AppTextField(
              label: 'Concepto',
              controller: _titleController,
              hint: 'Ej: Cena de equipo, gasolina...',
              prefixIcon: Icons.receipt_long_rounded,
              validator: (v) =>
                  v == null || v.trim().isEmpty ? 'Introduce el concepto' : null,
            ),
            const SizedBox(height: 16),
            AppTextField(
              label: 'Importe (€)',
              controller: _amountController,
              hint: '0.00',
              prefixIcon: Icons.euro_rounded,
              keyboardType:
                  const TextInputType.numberWithOptions(decimal: true),
              validator: (v) {
                if (v == null || v.isEmpty) return 'Introduce el importe';
                final n = double.tryParse(v.replaceAll(',', '.'));
                if (n == null || n <= 0) return 'Importe no válido';
                return null;
              },
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              value: _category,
              decoration: const InputDecoration(
                labelText: 'Categoría',
                prefixIcon: Icon(Icons.category_rounded),
              ),
              items: const [
                DropdownMenuItem(value: 'expense', child: Text('Gasto')),
                DropdownMenuItem(value: 'purchase', child: Text('Compra')),
                DropdownMenuItem(value: 'travel', child: Text('Desplazamiento')),
                DropdownMenuItem(value: 'other', child: Text('Otro')),
              ],
              onChanged: (v) => setState(() => _category = v ?? 'expense'),
            ),
            const SizedBox(height: 16),
            ListTile(
              contentPadding: EdgeInsets.zero,
              leading: Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: AppColors.neutral100,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(Icons.calendar_today_rounded,
                    size: 20, color: AppColors.primary),
              ),
              title: const Text('Fecha del gasto'),
              subtitle: Text(
                '${_date.day.toString().padLeft(2, '0')}/${_date.month.toString().padLeft(2, '0')}/${_date.year}',
              ),
              trailing: const Icon(Icons.chevron_right_rounded),
              onTap: () async {
                final picked = await showDatePicker(
                  context: context,
                  initialDate: _date,
                  firstDate: DateTime.now().subtract(const Duration(days: 365)),
                  lastDate: DateTime.now(),
                );
                if (picked != null) setState(() => _date = picked);
              },
            ),
            const SizedBox(height: 16),
            AppTextField(
              label: 'Descripción (opcional)',
              controller: _descriptionController,
              hint: 'Detalles adicionales...',
              prefixIcon: Icons.notes_rounded,
              maxLines: 3,
            ),
            const SizedBox(height: 32),
            AppButton(
              label: 'Crear ticket',
              onPressed: isLoading ? null : _submit,
              loading: isLoading,
              icon: Icons.add_rounded,
            ),
          ],
        ),
      ),
    );
  }
}

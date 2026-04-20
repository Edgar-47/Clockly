import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_colors.dart';
import '../../../core/utils/date_utils.dart';
import '../../../domain/entities/ticket_entity.dart';
import '../../../shared/extensions/context_extensions.dart';
import '../../../shared/widgets/app_button.dart';
import '../providers/tickets_provider.dart';
import '../../auth/providers/auth_provider.dart';

class TicketDetailScreen extends ConsumerWidget {
  const TicketDetailScreen({super.key, required this.ticketId});
  final int ticketId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(ticketsProvider).valueOrNull;
    final ticketModel = state?.tickets.firstWhere(
      (t) => t.id == ticketId,
      orElse: () => state!.tickets.first,
    );

    if (ticketModel == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Ticket')),
        body: const Center(child: Text('Ticket no encontrado')),
      );
    }

    final ticket = ticketModel.toEntity();
    final auth = ref.watch(authProvider).valueOrNull;
    final isAdmin = auth?.session?.activeBusiness?.isAdmin ?? false;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Detalle del ticket'),
        centerTitle: false,
      ),
      body: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          // Header
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppColors.neutral200),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(ticket.title,
                          style: Theme.of(context).textTheme.headlineSmall),
                    ),
                    _StatusChip(status: ticket.status),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  '€${ticket.amount.toStringAsFixed(2)}',
                  style: Theme.of(context).textTheme.displayMedium?.copyWith(
                        color: AppColors.primary,
                        fontWeight: FontWeight.w800,
                      ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // Details
          _DetailSection(children: [
            _DetailRow(
              icon: Icons.category_rounded,
              label: 'Categoría',
              value: _categoryLabel(ticket.category),
            ),
            _DetailRow(
              icon: Icons.calendar_today_rounded,
              label: 'Fecha',
              value: AppDateUtils.formatDate(ticket.date),
            ),
            _DetailRow(
              icon: Icons.schedule_rounded,
              label: 'Creado',
              value: AppDateUtils.formatDateTime(ticket.createdAt),
            ),
            if (ticket.employeeName != null)
              _DetailRow(
                icon: Icons.person_rounded,
                label: 'Empleado',
                value: ticket.employeeName!,
              ),
          ]),

          if (ticket.description != null && ticket.description!.isNotEmpty) ...[
            const SizedBox(height: 16),
            _DetailSection(children: [
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Descripción',
                        style: Theme.of(context).textTheme.labelLarge),
                    const SizedBox(height: 4),
                    Text(ticket.description!,
                        style: Theme.of(context).textTheme.bodyMedium),
                  ],
                ),
              ),
            ]),
          ],

          if (ticket.reviewNote != null && ticket.reviewNote!.isNotEmpty) ...[
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppColors.infoLight,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppColors.info.withOpacity(0.3)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Row(children: [
                    Icon(Icons.admin_panel_settings_rounded,
                        color: AppColors.info, size: 16),
                    SizedBox(width: 6),
                    Text('Nota del administrador',
                        style: TextStyle(
                            fontWeight: FontWeight.w600,
                            color: AppColors.info,
                            fontSize: 12)),
                  ]),
                  const SizedBox(height: 6),
                  Text(ticket.reviewNote!,
                      style: Theme.of(context).textTheme.bodyMedium),
                ],
              ),
            ),
          ],

          // Admin actions
          if (isAdmin && ticket.canBeReviewed) ...[
            const SizedBox(height: 32),
            Text('Revisar ticket',
                style: Theme.of(context)
                    .textTheme
                    .titleMedium
                    ?.copyWith(fontWeight: FontWeight.w700)),
            const SizedBox(height: 12),
            _AdminReviewButtons(ticketId: ticket.id),
          ],
        ],
      ),
    );
  }

  String _categoryLabel(TicketCategory c) => switch (c) {
        TicketCategory.expense => 'Gasto',
        TicketCategory.purchase => 'Compra',
        TicketCategory.travel => 'Desplazamiento',
        TicketCategory.other => 'Otro',
      };
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.status});
  final TicketStatus status;

  @override
  Widget build(BuildContext context) {
    final (label, color) = switch (status) {
      TicketStatus.approved => ('Aprobado', AppColors.success),
      TicketStatus.rejected => ('Rechazado', AppColors.error),
      TicketStatus.reimbursed => ('Reembolsado', AppColors.accent),
      TicketStatus.pending => ('Pendiente', AppColors.warning),
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(label,
          style: TextStyle(
              fontSize: 12, fontWeight: FontWeight.w600, color: color)),
    );
  }
}

class _DetailSection extends StatelessWidget {
  const _DetailSection({required this.children});
  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.neutral200),
      ),
      child: Column(children: children),
    );
  }
}

class _DetailRow extends StatelessWidget {
  const _DetailRow(
      {required this.icon, required this.label, required this.value});
  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Icon(icon, size: 18, color: AppColors.textHint),
          const SizedBox(width: 12),
          Text(label,
              style: Theme.of(context)
                  .textTheme
                  .bodyMedium
                  ?.copyWith(color: AppColors.textSecondary)),
          const Spacer(),
          Text(value, style: Theme.of(context).textTheme.labelLarge),
        ],
      ),
    );
  }
}

class _AdminReviewButtons extends ConsumerStatefulWidget {
  const _AdminReviewButtons({required this.ticketId});
  final int ticketId;

  @override
  ConsumerState<_AdminReviewButtons> createState() =>
      _AdminReviewButtonsState();
}

class _AdminReviewButtonsState extends ConsumerState<_AdminReviewButtons> {
  final _noteController = TextEditingController();

  @override
  void dispose() {
    _noteController.dispose();
    super.dispose();
  }

  Future<void> _review(String status) async {
    String? note;
    if (status == 'rejected') {
      note = await _showNoteDialog();
      if (note == null) return; // cancelled
    }
    final ok = await ref.read(ticketsProvider.notifier).reviewTicket(
          ticketId: widget.ticketId,
          status: status,
          reviewNote: note,
        );
    if (ok && mounted) {
      context.showSnackBar(status == 'approved' ? 'Ticket aprobado' : 'Ticket rechazado',
          isError: status == 'rejected');
      Navigator.pop(context);
    }
  }

  Future<String?> _showNoteDialog() => showDialog<String>(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Text('Motivo del rechazo'),
          content: TextField(
            controller: _noteController,
            decoration: const InputDecoration(hintText: 'Indica el motivo...'),
            maxLines: 3,
            autofocus: true,
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Cancelar'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(ctx, _noteController.text.trim()),
              style: FilledButton.styleFrom(backgroundColor: AppColors.error),
              child: const Text('Rechazar'),
            ),
          ],
        ),
      );

  @override
  Widget build(BuildContext context) {
    final isLoading =
        ref.watch(ticketsProvider).valueOrNull?.actionLoading ?? false;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        AppButton(
          label: 'Aprobar ticket',
          onPressed: isLoading ? null : () => _review('approved'),
          loading: isLoading,
          icon: Icons.check_circle_rounded,
        ),
        const SizedBox(height: 10),
        AppButton(
          label: 'Rechazar',
          onPressed: isLoading ? null : () => _review('rejected'),
          variant: AppButtonVariant.danger,
          icon: Icons.cancel_rounded,
        ),
      ],
    );
  }
}

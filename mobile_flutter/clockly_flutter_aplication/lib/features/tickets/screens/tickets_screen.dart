import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/app_colors.dart';
import '../../../core/utils/date_utils.dart';
import '../../../domain/entities/ticket_entity.dart';
import '../../../shared/widgets/empty_state.dart';
import '../../../shared/widgets/error_view.dart';
import '../providers/tickets_provider.dart';

class TicketsScreen extends ConsumerWidget {
  const TicketsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final asyncState = ref.watch(ticketsProvider);

    return Scaffold(
      body: asyncState.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => ErrorView(
          message: e.toString(),
          onRetry: () => ref.invalidate(ticketsProvider),
        ),
        data: (state) => _buildBody(context, ref, state),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => context.push('/tickets/create'),
        icon: const Icon(Icons.add_rounded),
        label: const Text('Nuevo ticket'),
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
      ),
    );
  }

  Widget _buildBody(BuildContext context, WidgetRef ref, TicketsState state) {
    return CustomScrollView(
      slivers: [
        SliverAppBar(
          floating: true,
          backgroundColor: AppColors.background,
          title:
              Text('Tickets', style: Theme.of(context).textTheme.headlineSmall),
          actions: [
            IconButton(
              icon: const Icon(Icons.filter_list_rounded),
              onPressed: () => _showFilterSheet(context, ref, state),
            ),
          ],
        ),
        if (state.filterStatus != null)
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 4, 16, 0),
              child: Wrap(
                spacing: 8,
                children: [
                  Chip(
                    label: Text(
                        'Estado: ${_statusLabel(state.filterStatus!)}',
                        style: const TextStyle(fontSize: 12)),
                    deleteIcon: const Icon(Icons.close, size: 14),
                    onDeleted: () =>
                        ref.read(ticketsProvider.notifier).applyFilter(),
                  ),
                ],
              ),
            ),
          ),
        if (state.loading)
          const SliverFillRemaining(
              child: Center(child: CircularProgressIndicator()))
        else if (state.tickets.isEmpty)
          const SliverFillRemaining(
            child: EmptyState(
              title: 'Sin tickets',
              subtitle: 'No tienes gastos o tickets registrados todavía.',
              icon: Icons.receipt_long_outlined,
              actionLabel: 'Crear ticket',
            ),
          )
        else
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 100),
            sliver: SliverList(
              delegate: SliverChildBuilderDelegate(
                (ctx, i) {
                  final ticket = state.tickets[i].toEntity();
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 10),
                    child: _TicketCard(
                      ticket: ticket,
                      onTap: () => context.push('/tickets/${ticket.id}'),
                    ),
                  );
                },
                childCount: state.tickets.length,
              ),
            ),
          ),
      ],
    );
  }

  void _showFilterSheet(
      BuildContext context, WidgetRef ref, TicketsState state) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (ctx) => Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text('Filtrar tickets',
                style: Theme.of(ctx).textTheme.headlineSmall),
            const SizedBox(height: 20),
            for (final s in ['pending', 'approved', 'rejected', 'reimbursed'])
              ListTile(
                leading: _StatusDot(statusStr: s),
                title: Text(_statusLabel(s)),
                trailing: state.filterStatus == s
                    ? const Icon(Icons.check_rounded, color: AppColors.primary)
                    : null,
                onTap: () {
                  Navigator.pop(ctx);
                  ref.read(ticketsProvider.notifier).applyFilter(status: s);
                },
              ),
            const Divider(),
            ListTile(
              leading: const Icon(Icons.clear_all_rounded),
              title: const Text('Mostrar todos'),
              onTap: () {
                Navigator.pop(ctx);
                ref.read(ticketsProvider.notifier).applyFilter();
              },
            ),
          ],
        ),
      ),
    );
  }

  String _statusLabel(String s) => switch (s) {
        'approved' => 'Aprobado',
        'rejected' => 'Rechazado',
        'reimbursed' => 'Reembolsado',
        _ => 'Pendiente',
      };
}

class _TicketCard extends StatelessWidget {
  const _TicketCard({required this.ticket, required this.onTap});
  final TicketEntity ticket;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppColors.neutral200),
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: _categoryColor(ticket.category).withOpacity(0.12),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(
                _categoryIcon(ticket.category),
                color: _categoryColor(ticket.category),
                size: 20,
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(ticket.title,
                      style: Theme.of(context).textTheme.titleMedium,
                      overflow: TextOverflow.ellipsis),
                  const SizedBox(height: 2),
                  Text(AppDateUtils.formatDate(ticket.date),
                      style: Theme.of(context).textTheme.bodySmall),
                ],
              ),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  '€${ticket.amount.toStringAsFixed(2)}',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w700,
                      ),
                ),
                const SizedBox(height: 4),
                _StatusBadge(status: ticket.status),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Color _categoryColor(TicketCategory c) => switch (c) {
        TicketCategory.expense => AppColors.warning,
        TicketCategory.purchase => AppColors.primary,
        TicketCategory.travel => AppColors.accent,
        TicketCategory.other => AppColors.neutral500,
      };

  IconData _categoryIcon(TicketCategory c) => switch (c) {
        TicketCategory.expense => Icons.payments_rounded,
        TicketCategory.purchase => Icons.shopping_bag_rounded,
        TicketCategory.travel => Icons.directions_car_rounded,
        TicketCategory.other => Icons.receipt_rounded,
      };
}

class _StatusBadge extends StatelessWidget {
  const _StatusBadge({required this.status});
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
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
      decoration: BoxDecoration(
        color: color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(label,
          style: TextStyle(
              fontSize: 10, fontWeight: FontWeight.w600, color: color)),
    );
  }
}

class _StatusDot extends StatelessWidget {
  const _StatusDot({required this.statusStr});
  final String statusStr;

  @override
  Widget build(BuildContext context) {
    final color = switch (statusStr) {
      'approved' => AppColors.success,
      'rejected' => AppColors.error,
      'reimbursed' => AppColors.accent,
      _ => AppColors.warning,
    };
    return Container(
        width: 12,
        height: 12,
        decoration: BoxDecoration(color: color, shape: BoxShape.circle));
  }
}

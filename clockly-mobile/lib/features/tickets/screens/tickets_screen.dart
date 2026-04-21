import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/utils/date_utils.dart';
import '../../../domain/entities/ticket_entity.dart';
import '../../../shared/widgets/brand_logo.dart';
import '../../../shared/widgets/empty_state.dart';
import '../../../shared/widgets/error_view.dart';
import '../../../shared/widgets/premium_components.dart';
import '../providers/tickets_provider.dart';

class TicketsScreen extends ConsumerWidget {
  const TicketsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final asyncState = ref.watch(ticketsProvider);

    return Scaffold(
      body: ClocklyBackground(
        child: SafeArea(
          bottom: false,
          child: asyncState.when(
            loading: () => const Center(
              child: CircularProgressIndicator(color: AppColors.cobaltLight),
            ),
            error: (e, _) => ErrorView(
              message: e.toString(),
              onRetry: () => ref.invalidate(ticketsProvider),
            ),
            data: (state) => _TicketsBody(state: state, ref: ref),
          ),
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => context.push('/tickets/create'),
        icon: const Icon(Icons.add_rounded),
        label: const Text('Ticket'),
        backgroundColor: AppColors.cobalt,
        foregroundColor: Colors.white,
      ),
    );
  }
}

class _TicketsBody extends StatelessWidget {
  const _TicketsBody({required this.state, required this.ref});

  final TicketsState state;
  final WidgetRef ref;

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: () => ref.read(ticketsProvider.notifier).refresh(),
      child: CustomScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        slivers: [
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(22, 10, 22, 136),
            sliver: SliverList(
              delegate: SliverChildListDelegate([
                _TicketsHeader(
                  onFilter: () => _showFilterSheet(context, ref, state),
                ),
                const SizedBox(height: AppSpacing.x2),
                if (state.filterStatus != null) ...[
                  GlassCard(
                    padding: const EdgeInsets.symmetric(
                      horizontal: AppSpacing.md,
                      vertical: AppSpacing.sm,
                    ),
                    child: Row(
                      children: [
                        StatusPill(
                          label: _statusLabel(state.filterStatus!),
                          color: _statusColor(state.filterStatus!),
                          compact: true,
                        ),
                        const Spacer(),
                        IconButton(
                          visualDensity: VisualDensity.compact,
                          onPressed: () =>
                              ref.read(ticketsProvider.notifier).applyFilter(),
                          icon: const Icon(Icons.close_rounded,
                              color: AppColors.paper),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: AppSpacing.lg),
                ],
                if (state.loading)
                  const Padding(
                    padding: EdgeInsets.only(top: 110),
                    child: Center(
                      child: CircularProgressIndicator(
                        color: AppColors.cobaltLight,
                      ),
                    ),
                  )
                else if (state.tickets.isEmpty)
                  EmptyState(
                    title: 'Sin tickets',
                    subtitle: 'No tienes gastos o tickets registrados todavía.',
                    icon: Icons.receipt_long_outlined,
                    actionLabel: 'Crear ticket',
                    onAction: () => context.push('/tickets/create'),
                  )
                else
                  ...state.tickets.map((ticketModel) {
                    final ticket = ticketModel.toEntity();
                    return Padding(
                      padding: const EdgeInsets.only(bottom: AppSpacing.md),
                      child: _TicketCard(
                        ticket: ticket,
                        onTap: () => context.push('/tickets/${ticket.id}'),
                      ),
                    );
                  }),
              ]),
            ),
          ),
        ],
      ),
    );
  }

  void _showFilterSheet(
    BuildContext context,
    WidgetRef ref,
    TicketsState state,
  ) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (ctx) => Container(
        decoration: const BoxDecoration(
          color: AppColors.paper,
          borderRadius: BorderRadius.vertical(top: Radius.circular(30)),
        ),
        padding: const EdgeInsets.fromLTRB(22, 12, 22, 26),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Center(
              child: Container(
                width: 42,
                height: 5,
                margin: const EdgeInsets.only(bottom: AppSpacing.xl),
                decoration: BoxDecoration(
                  color: AppColors.neutral300,
                  borderRadius: BorderRadius.circular(AppRadius.pill),
                ),
              ),
            ),
            Text('Filtrar tickets',
                style: Theme.of(ctx).textTheme.headlineSmall),
            const SizedBox(height: AppSpacing.lg),
            for (final s in ['pending', 'approved', 'rejected', 'reimbursed'])
              ListTile(
                contentPadding: const EdgeInsets.symmetric(horizontal: 4),
                leading: PremiumIconBox(
                  icon: Icons.circle_rounded,
                  color: _statusColor(s),
                  size: 36,
                ),
                title: Text(_statusLabel(s)),
                trailing: state.filterStatus == s
                    ? const Icon(Icons.check_rounded, color: AppColors.cobalt)
                    : null,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                ),
                onTap: () {
                  Navigator.pop(ctx);
                  ref.read(ticketsProvider.notifier).applyFilter(status: s);
                },
              ),
            const Divider(height: 24),
            ListTile(
              contentPadding: const EdgeInsets.symmetric(horizontal: 4),
              leading: const PremiumIconBox(
                icon: Icons.clear_all_rounded,
                color: AppColors.neutral500,
                size: 36,
              ),
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
}

class _TicketsHeader extends StatelessWidget {
  const _TicketsHeader({required this.onFilter});

  final VoidCallback onFilter;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        const ClocklyBrandLogo(
          variant: ClocklyLogoVariant.mark,
          markSize: 34,
          inverse: true,
        ),
        const SizedBox(width: AppSpacing.md),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Tickets',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                      color: AppColors.paper,
                    ),
              ),
              Text(
                'Gastos y revisiones',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Colors.white.withOpacity(0.58),
                    ),
              ),
            ],
          ),
        ),
        IconButton.filled(
          onPressed: onFilter,
          style: IconButton.styleFrom(
            backgroundColor: Colors.white.withOpacity(0.08),
            foregroundColor: AppColors.paper,
          ),
          icon: const Icon(Icons.tune_rounded),
          tooltip: 'Filtrar',
        ),
      ],
    );
  }
}

class _TicketCard extends StatelessWidget {
  const _TicketCard({required this.ticket, required this.onTap});

  final TicketEntity ticket;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return PremiumCard(
      padding: const EdgeInsets.all(AppSpacing.lg),
      onTap: onTap,
      child: Row(
        children: [
          PremiumIconBox(
            icon: _categoryIcon(ticket.category),
            color: _categoryColor(ticket.category),
          ),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  ticket.title,
                  style: Theme.of(context).textTheme.titleMedium,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 3),
                Text(
                  AppDateUtils.formatDate(ticket.date),
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ),
          const SizedBox(width: AppSpacing.sm),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                '€${ticket.amount.toStringAsFixed(2)}',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w900,
                    ),
              ),
              const SizedBox(height: 6),
              StatusPill(
                label: _statusLabel(ticket.status.name),
                color: _ticketStatusColor(ticket.status),
                compact: true,
              ),
            ],
          ),
        ],
      ),
    );
  }

  Color _categoryColor(TicketCategory c) => switch (c) {
        TicketCategory.expense => AppColors.amber,
        TicketCategory.purchase => AppColors.cobalt,
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

String _statusLabel(String s) => switch (s) {
      'approved' => 'Aprobado',
      'rejected' => 'Rechazado',
      'reimbursed' => 'Reembolsado',
      _ => 'Pendiente',
    };

Color _statusColor(String s) => switch (s) {
      'approved' => AppColors.verde,
      'rejected' => AppColors.rose,
      'reimbursed' => AppColors.cobalt,
      _ => AppColors.amber,
    };

Color _ticketStatusColor(TicketStatus status) => switch (status) {
      TicketStatus.approved => AppColors.verde,
      TicketStatus.rejected => AppColors.rose,
      TicketStatus.reimbursed => AppColors.cobalt,
      TicketStatus.pending => AppColors.amber,
    };

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../domain/entities/business_entity.dart';
import '../../../shared/extensions/context_extensions.dart';
import '../../../shared/widgets/brand_logo.dart';
import '../../../shared/widgets/empty_state.dart';
import '../../../shared/widgets/premium_components.dart';
import '../../auth/providers/auth_provider.dart';

class BusinessSelectorScreen extends ConsumerWidget {
  const BusinessSelectorScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authProvider).valueOrNull;
    final session = auth?.session;
    final businesses = session?.businessEntities ?? [];
    final activeId = session?.activeBusinessId;

    return Scaffold(
      body: ClocklyBackground(
        child: SafeArea(
          bottom: false,
          child: CustomScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            slivers: [
              SliverPadding(
                padding: const EdgeInsets.fromLTRB(22, 10, 22, 126),
                sliver: SliverList(
                  delegate: SliverChildListDelegate([
                    const _BusinessHeader(),
                    const SizedBox(height: AppSpacing.x2),
                    if (businesses.isEmpty)
                      const EmptyState(
                        title: 'Sin negocios',
                        subtitle: 'No tienes negocios asignados.',
                        icon: Icons.storefront_rounded,
                      )
                    else
                      ...businesses.map((biz) {
                        final isActive = biz.id == activeId;
                        return Padding(
                          padding:
                              const EdgeInsets.only(bottom: AppSpacing.md),
                          child: _BusinessTile(
                            business: biz,
                            isActive: isActive,
                            onTap: isActive
                                ? null
                                : () async {
                                    await ref
                                        .read(authProvider.notifier)
                                        .switchBusiness(biz.id);
                                    if (context.mounted) {
                                      context.showSnackBar(
                                        'Cambiado a ${biz.name}',
                                      );
                                      context.go('/attendance');
                                    }
                                  },
                          ),
                        );
                      }),
                  ]),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _BusinessHeader extends StatelessWidget {
  const _BusinessHeader();

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
                'Negocios',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                      color: AppColors.paper,
                    ),
              ),
              Text(
                'Selecciona el contexto de trabajo',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Colors.white.withOpacity(0.58),
                    ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _BusinessTile extends StatelessWidget {
  const _BusinessTile({
    required this.business,
    required this.isActive,
    this.onTap,
  });

  final BusinessEntity business;
  final bool isActive;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return PremiumCard(
      onTap: onTap,
      color: isActive ? AppColors.cobaltSoft : AppColors.card,
      borderColor: isActive ? AppColors.cobalt : AppColors.neutral200,
      child: Row(
        children: [
          PremiumIconBox(
            icon: Icons.storefront_rounded,
            color: isActive ? AppColors.cobalt : AppColors.neutral500,
            size: 44,
          ),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  business.name,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight:
                            isActive ? FontWeight.w900 : FontWeight.w700,
                      ),
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 3),
                Text(
                  '${_typeLabel(business.type)} · ${business.timezone}',
                  style: Theme.of(context).textTheme.bodySmall,
                  overflow: TextOverflow.ellipsis,
                ),
                if (business.role != null) ...[
                  const SizedBox(height: AppSpacing.sm),
                  StatusPill(
                    label: _roleLabel(business.role!),
                    color: AppColors.cobalt,
                    compact: true,
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(width: AppSpacing.sm),
          Icon(
            isActive
                ? Icons.check_circle_rounded
                : Icons.chevron_right_rounded,
            color: isActive ? AppColors.cobalt : AppColors.neutral400,
          ),
        ],
      ),
    );
  }

  String _typeLabel(String t) => switch (t) {
        'restaurant' => 'Restaurante',
        'retail' => 'Retail',
        'office' => 'Oficina',
        _ => 'Empresa',
      };

  String _roleLabel(String r) => switch (r) {
        'admin' => 'Administrador',
        'manager' => 'Manager',
        _ => 'Empleado',
      };
}

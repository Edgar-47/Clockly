import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/app_colors.dart';
import '../../../domain/entities/business_entity.dart';
import '../../../shared/extensions/context_extensions.dart';
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
      appBar: AppBar(
        title: const Text('Negocios'),
        centerTitle: false,
      ),
      body: businesses.isEmpty
          ? const Center(child: Text('No tienes negocios asignados.'))
          : ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: businesses.length,
              separatorBuilder: (_, __) => const SizedBox(height: 10),
              itemBuilder: (ctx, i) {
                final biz = businesses[i];
                final isActive = biz.id == activeId;
                return _BusinessTile(
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
                                'Cambiado a ${biz.name}');
                            context.go('/attendance');
                          }
                        },
                );
              },
            ),
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
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: isActive ? AppColors.primarySurface : AppColors.surface,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: isActive ? AppColors.primary : AppColors.neutral200,
            width: isActive ? 2 : 1,
          ),
        ),
        child: Row(
          children: [
            Container(
              width: 44,
              height: 44,
              decoration: BoxDecoration(
                color: AppColors.primary.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Icon(Icons.business_rounded,
                  color: AppColors.primary, size: 22),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(business.name,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight:
                                isActive ? FontWeight.w700 : FontWeight.w500,
                          )),
                  Text(
                    '${_typeLabel(business.type)} · ${business.timezone}',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                  if (business.role != null) ...[
                    const SizedBox(height: 2),
                    Text(
                      _roleLabel(business.role!),
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                        color: AppColors.primary,
                      ),
                    ),
                  ],
                ],
              ),
            ),
            if (isActive)
              const Icon(Icons.check_circle_rounded,
                  color: AppColors.primary, size: 22),
          ],
        ),
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

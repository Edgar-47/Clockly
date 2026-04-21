import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../shared/extensions/context_extensions.dart';
import '../../../shared/widgets/brand_logo.dart';
import '../../../shared/widgets/premium_components.dart';
import '../../../shared/widgets/user_avatar.dart';
import '../../auth/providers/auth_provider.dart';

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authProvider).valueOrNull;
    final user = auth?.session?.userEntity;
    final business = auth?.session?.activeBusiness;

    return Scaffold(
      body: ClocklyBackground(
        child: SafeArea(
          bottom: false,
          child: CustomScrollView(
            slivers: [
              SliverPadding(
                padding: const EdgeInsets.fromLTRB(22, 10, 22, 126),
                sliver: SliverList(
                  delegate: SliverChildListDelegate([
                    const _SettingsHeader(),
                    const SizedBox(height: AppSpacing.x2),
                    if (user != null) ...[
                      _ProfileCard(
                        name: user.fullName,
                        identifier: user.identifier,
                        email: user.email,
                        avatarUrl: user.avatarUrl,
                        initials: user.initials,
                        role: _businessRoleLabel(business?.role),
                      ),
                      const SizedBox(height: AppSpacing.lg),
                    ],
                    if (business != null) ...[
                      _SettingsTile(
                        icon: Icons.storefront_rounded,
                        title: business.name,
                        subtitle: 'Negocio activo',
                        color: AppColors.cobalt,
                        onTap: () => context.push('/business'),
                      ),
                      const SizedBox(height: AppSpacing.x2),
                    ],
                    const PremiumSectionHeader(
                      title: 'Cuenta',
                      subtitle: 'Preferencias y herramientas',
                      inverse: true,
                    ),
                    const SizedBox(height: AppSpacing.md),
                    _SettingsTile(
                      icon: Icons.workspace_premium_rounded,
                      title: 'Mi suscripción',
                      subtitle: 'Plan, límites y opciones',
                      color: AppColors.amber,
                      onTap: () => context.push('/subscriptions'),
                    ),
                    _SettingsTile(
                      icon: Icons.tablet_mac_rounded,
                      title: 'Modo kiosko',
                      subtitle: 'Fichaje compartido en tablet',
                      color: AppColors.verde,
                      onTap: () => context.push('/kiosk'),
                    ),
                    const SizedBox(height: AppSpacing.x2),
                    const PremiumSectionHeader(
                      title: 'Aplicación',
                      subtitle: 'Información y seguridad',
                      inverse: true,
                    ),
                    const SizedBox(height: AppSpacing.md),
                    const _SettingsTile(
                      icon: Icons.info_outline_rounded,
                      title: 'Versión',
                      subtitle: '1.0.0 (build 1)',
                      color: AppColors.neutral500,
                    ),
                    _SettingsTile(
                      icon: Icons.privacy_tip_outlined,
                      title: 'Política de privacidad',
                      subtitle: 'Información legal',
                      color: AppColors.cobalt,
                      onTap: () {},
                    ),
                    const SizedBox(height: AppSpacing.x2),
                    _SettingsTile(
                      icon: Icons.logout_rounded,
                      title: 'Cerrar sesión',
                      subtitle: 'Salir de ClockLy en este dispositivo',
                      color: AppColors.rose,
                      destructive: true,
                      onTap: () async {
                        final confirmed = await context.showConfirmDialog(
                          title: 'Cerrar sesión',
                          message: '¿Seguro que quieres salir?',
                          confirmLabel: 'Salir',
                          destructive: true,
                        );
                        if (confirmed == true) {
                          ref.read(authProvider.notifier).logout();
                        }
                      },
                    ),
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

String? _businessRoleLabel(String? role) {
  return switch (role) {
    'admin' => 'Administrador',
    'manager' => 'Manager',
    'employee' => 'Empleado',
    null || '' => null,
    _ => role,
  };
}

class _SettingsHeader extends StatelessWidget {
  const _SettingsHeader();

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
                'Perfil',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                      color: AppColors.paper,
                    ),
              ),
              Text(
                'Cuenta, negocio y ajustes',
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

class _ProfileCard extends StatelessWidget {
  const _ProfileCard({
    required this.name,
    required this.identifier,
    required this.email,
    required this.avatarUrl,
    required this.initials,
    this.role,
  });

  final String name;
  final String identifier;
  final String? email;
  final String? avatarUrl;
  final String initials;
  final String? role;

  @override
  Widget build(BuildContext context) {
    return PremiumCard(
      color: AppColors.paper,
      child: Row(
        children: [
          UserAvatar(
            initials: initials,
            imageUrl: avatarUrl,
            size: 58,
            color: AppColors.cobalt,
          ),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  name,
                  style: Theme.of(context).textTheme.titleLarge,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 3),
                Text(
                  email?.isNotEmpty == true ? email! : identifier,
                  style: Theme.of(context).textTheme.bodySmall,
                  overflow: TextOverflow.ellipsis,
                ),
                if (role != null) ...[
                  const SizedBox(height: AppSpacing.sm),
                  StatusPill(
                    label: role!,
                    color: AppColors.cobalt,
                    compact: true,
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _SettingsTile extends StatelessWidget {
  const _SettingsTile({
    required this.icon,
    required this.title,
    required this.color,
    this.subtitle,
    this.onTap,
    this.destructive = false,
  });

  final IconData icon;
  final String title;
  final String? subtitle;
  final Color color;
  final VoidCallback? onTap;
  final bool destructive;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.md),
      child: PremiumCard(
        padding: const EdgeInsets.all(AppSpacing.lg),
        onTap: onTap,
        color: destructive ? AppColors.roseSoft : AppColors.card,
        borderColor:
            destructive ? AppColors.rose.withOpacity(0.22) : AppColors.neutral200,
        child: Row(
          children: [
            PremiumIconBox(icon: icon, color: color, size: 40),
            const SizedBox(width: AppSpacing.md),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          color: destructive
                              ? AppColors.rose
                              : AppColors.textPrimary,
                        ),
                  ),
                  if (subtitle != null) ...[
                    const SizedBox(height: 2),
                    Text(
                      subtitle!,
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ],
                ],
              ),
            ),
            if (onTap != null)
              Icon(
                Icons.chevron_right_rounded,
                color: destructive ? AppColors.rose : AppColors.neutral400,
              ),
          ],
        ),
      ),
    );
  }
}
